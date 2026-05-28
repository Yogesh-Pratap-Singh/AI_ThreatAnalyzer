import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.deps import get_db, get_current_user
from app.models.all_models import Alert, AnalystFeedback, ThreatExplanation, User
from app.schemas.all_schemas import FeedbackRequest

router = APIRouter(prefix="/feedback", tags=["feedback"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Fetch Alert to get signature
    query = select(Alert).where(Alert.id == payload.alert_id)
    result = await db.execute(query)
    alert = result.scalars().first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reference alert not found."
        )

    # 2. Insert Analyst Feedback record
    fb = AnalystFeedback(
        id=uuid.uuid4(),
        alert_id=payload.alert_id,
        user_id=current_user.id,
        feedback_type=payload.feedback_type,
        fp_reason=payload.fp_reason,
        notes=payload.notes,
        alert_signature=alert.alert_signature
    )
    db.add(fb)
    
    # 3. Update ThreatExplanation counts if rating LLM output
    if payload.feedback_type in ["explanation_helpful", "explanation_not_helpful"]:
        exp_query = select(ThreatExplanation).where(
            ThreatExplanation.alert_signature == alert.alert_signature
        )
        exp_result = await db.execute(exp_query)
        explanation = exp_result.scalars().first()
        
        if explanation:
            if payload.feedback_type == "explanation_helpful":
                explanation.helpful_count += 1
            else:
                explanation.not_helpful_count += 1
                
    await db.commit()
    return {"ok": True}
