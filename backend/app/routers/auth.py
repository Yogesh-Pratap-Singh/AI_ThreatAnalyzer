from datetime import datetime, timedelta
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.deps import get_db, get_current_user
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_refresh_token
from app.core.cache import cache
from app.models.all_models import User, Session
from app.schemas.all_schemas import LoginRequest, LoginResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])

def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    # Set access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="strict",
        max_age=900  # 15 minutes
    )
    # Set refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="strict",
        max_age=28800  # 8 hours
    )

def clear_auth_cookies(response: Response):
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    client_ip = request.client.host if request.client else "unknown"
    fail_key = f"login_fail_ip:{client_ip}"
    
    # 1. Check Rate Limit
    fail_count_str = await cache.get(fail_key)
    if fail_count_str and int(fail_count_str) >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account locked for 15 minutes due to too many failed attempts."
        )

    # 2. Query User
    query = select(User).where(User.email == login_data.email)
    result = await db.execute(query)
    user = result.scalars().first()

    # 3. Verify User & Password
    if not user or not verify_password(login_data.password, user.password_hash):
        # Increment Rate Limit Counter
        curr_fails = await cache.incr(fail_key)
        if curr_fails == 1:
            await cache.expire(fail_key, 900)  # 15-minute lock duration
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated."
        )

    # Reset Login Fails
    await cache.delete(fail_key)

    # 4. Create Active Session
    session_id = uuid.uuid4()
    expires_at = datetime.utcnow() + timedelta(hours=settings.REFRESH_TOKEN_EXPIRE_HOURS)
    
    # User info for JWT
    subject = {
        "id": str(user.id),
        "email": user.email,
        "role": user.role
    }
    
    access_token = create_access_token(subject)
    refresh_token = create_refresh_token(subject, session_id)
    
    # Store session in database (hashing refresh token for security)
    refresh_token_hash = get_password_hash(refresh_token)
    user_agent = request.headers.get("user-agent")
    
    db_session = Session(
        id=session_id,
        user_id=user.id,
        refresh_token_hash=refresh_token_hash,
        user_agent=user_agent[:500] if user_agent else None,
        ip_address=client_ip,
        expires_at=expires_at
    )
    db.add(db_session)
    
    # Update last login time
    user.last_login_at = datetime.utcnow()
    await db.commit()

    # 5. Set Cookies & Return Response
    set_auth_cookies(response, access_token, refresh_token)
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    }

@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token"
        )
    
    try:
        payload = decode_refresh_token(refresh_token)
        session_id = payload.get("session_id")
    except ValueError as e:
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        ) from e
        
    # Check session in database
    query = select(Session).where(Session.id == session_id).join(User)
    result = await db.execute(query)
    db_session = result.scalars().first()
    
    if not db_session or db_session.expires_at < datetime.utcnow():
        if db_session:
            await db.delete(db_session)
            await db.commit()
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or is invalid"
        )

    # Verify matching user
    user = db_session.user
    if not user or not user.is_active:
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )

    # Generate new access token
    subject = {
        "id": str(user.id),
        "email": user.email,
        "role": user.role
    }
    
    access_token = create_access_token(subject)
    
    # Update session expiry
    db_session.expires_at = datetime.utcnow() + timedelta(hours=settings.REFRESH_TOKEN_EXPIRE_HOURS)
    db_session.updated_at = datetime.utcnow()
    await db.commit()
    
    set_auth_cookies(response, access_token, refresh_token)
    return {"ok": True}

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        try:
            payload = decode_refresh_token(refresh_token)
            session_id = payload.get("session_id")
            
            # Delete session from DB
            query = select(Session).where(Session.id == session_id)
            result = await db.execute(query)
            db_session = result.scalars().first()
            if db_session:
                await db.delete(db_session)
                await db.commit()
        except Exception:
            pass
            
    clear_auth_cookies(response)
    return {"ok": True}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
