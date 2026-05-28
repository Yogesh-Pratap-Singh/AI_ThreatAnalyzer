import hashlib
import time
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.deps import get_db
from app.core.queue import queue_hub
from app.core.cache import cache
from app.models.all_models import DataSource
from app.schemas.all_schemas import IngestRequest

router = APIRouter(prefix="/ingest", tags=["ingestion"])

def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
async def ingest_events(
    payload: IngestRequest,
    x_source_api_key: str = Header(..., alias="X-Source-API-Key"),
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch data source from DB
    query = select(DataSource).where(DataSource.id == payload.source_id)
    result = await db.execute(query)
    data_source = result.scalars().first()
    
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configured data source not found."
        )

    # 2. Validate API Key Hash
    incoming_hash = hash_key(x_source_api_key)
    if data_source.api_key_hash != incoming_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid source API key credentials."
        )
        
    if data_source.status == "disconnected":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Data source is currently deactivated."
        )

    # 3. Enforce Rate Limiting (10,000 events per minute)
    minute_bin = int(time.time() // 60)
    rate_key = f"rate:ingest:{data_source.id}:{minute_bin}"
    
    curr_total_str = await cache.get(rate_key)
    curr_total = int(curr_total_str) if curr_total_str else 0
    
    new_event_count = len(payload.events)
    if curr_total + new_event_count > 10000:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 10,000 events per minute per source key."
        )
        
    # Increment counter
    await cache.set(rate_key, str(curr_total + new_event_count), ex=120)

    # 4. Push events onto raw queue
    for event in payload.events:
        event_dict = event.model_dump()
        event_dict["source_id"] = str(data_source.id)
        # Convert timestamp datetime to ISO format string for queue JSON serializability
        event_dict["timestamp"] = event.timestamp.isoformat()
        await queue_hub.publish_raw(event_dict)

    # Update last active time for source
    data_source.last_event_at = datetime.utcnow()
    await db.commit()

    return {"accepted": new_event_count}
