import asyncio
import json
import logging
from datetime import datetime
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func, and_

from app.core.deps import get_db, get_current_user
from app.core.queue import queue_hub
from app.models.all_models import Alert, Event, alert_events, AnalystNote, AnalystFeedback, User
from app.schemas.all_schemas import (
    AlertResponse, AlertListResponse, AlertDetailResponse, AlertDetailContainer, 
    AlertActionRequest, NoteRequest, NoteResponse, RelatedEventResponse
)
from app.services.explanation_service import get_or_generate_explanation

router = APIRouter(prefix="/alerts", tags=["alerts"])
logger = logging.getLogger("alerts_router")

@router.get("", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    severity: Optional[str] = Query(None, description="Comma-separated severity list (critical,high)"),
    status: Optional[str] = Query("open", description="Alert status (open, escalated, dismissed, false_positive, resolved)"),
    source_ip: Optional[str] = Query(None),
    mitre_tactic: Optional[str] = Query(None),
    from_time: Optional[datetime] = Query(None),
    to_time: Optional[datetime] = Query(None),
    sort: str = Query("severity_desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Base query
    base_stmt = select(Alert)
    
    # Filtering conditions
    filters = []
    if status and status.lower() != "all":
        filters.append(Alert.status == status.lower())
    if severity:
        severities = [s.strip().lower() for s in severity.split(",")]
        filters.append(Alert.severity.in_(severities))
    if source_ip:
        filters.append(Alert.source_ip == source_ip)
    if mitre_tactic:
        filters.append(Alert.mitre_tactic.ilike(f"%{mitre_tactic}%"))
    if from_time:
        filters.append(Alert.created_at >= from_time)
    if to_time:
        filters.append(Alert.created_at <= to_time)
        
    if filters:
        base_stmt = base_stmt.where(and_(*filters))
        
    # Total count query
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    count_result = await db.execute(count_stmt)
    total_count = count_result.scalar() or 0
    
    # Sorting
    if sort == "severity_desc":
        base_stmt = base_stmt.order_by(desc(Alert.severity_score))
    elif sort == "created_at_desc":
        base_stmt = base_stmt.order_by(desc(Alert.created_at))
    else:
        base_stmt = base_stmt.order_by(desc(Alert.severity_score))
        
    # Pagination
    offset = (page - 1) * limit
    stmt = base_stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    alerts = result.scalars().all()
    
    pages = (total_count + limit - 1) // limit
    
    return {
        "alerts": alerts,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": pages
        }
    }

@router.get("/stream")
async def stream_alerts(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Establishes a Server-Sent Events (SSE) connection to push real-time alerts to the client."""
    listener_queue = queue_hub.register_alert_listener()
    logger.info(f"Registered real-time SSE stream listener for user: {current_user.email}")
    
    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    logger.info("SSE client disconnected.")
                    break
                try:
                    # Non-blocking wait with timeout for heartbeat
                    alert_data = await asyncio.wait_for(listener_queue.get(), timeout=5.0)
                    yield f"event: {alert_data.get('event')}\ndata: {json.dumps(alert_data.get('data'))}\n\n"
                    listener_queue.task_done()
                except asyncio.TimeoutError:
                    # Send periodic heartbeat to keep connection alive
                    yield "event: heartbeat\ndata: {}\n\n"
        finally:
            queue_hub.unregister_alert_listener(listener_queue)
            logger.info(f"Unregistered SSE stream listener for user: {current_user.email}")

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/{alert_id}", response_model=AlertDetailContainer)
async def get_alert_detail(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch Alert
    alert_query = select(Alert).where(Alert.id == alert_id)
    alert_result = await db.execute(alert_query)
    alert = alert_result.scalars().first()
    
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
        
    # Fetch Related Events (ordered by time desc)
    events_query = (
        select(Event)
        .join(alert_events)
        .where(alert_events.c.alert_id == alert_id)
        .order_by(desc(Event.event_time))
    )
    events_result = await db.execute(events_query)
    related_events = events_result.scalars().all()
    
    # Fetch Notes (pre-populated)
    notes_query = (
        select(AnalystNote)
        .where(AnalystNote.alert_id == alert_id)
        .order_by(AnalystNote.created_at)
    )
    notes_result = await db.execute(notes_query)
    notes = notes_result.scalars().all()
    
    # Formulate detail response
    mitre_tech_name = alert.mitre_tactic  # Default
    if alert.mitre_technique_id == "T1048.003":
        mitre_tech_name = "Exfiltration Over Alternative Protocol"
    elif alert.mitre_technique_id == "T1071.001":
        mitre_tech_name = "Application Layer Protocol"
    elif alert.mitre_technique_id == "T1021.001":
        mitre_tech_name = "Remote Desktop Protocol"
    elif alert.mitre_technique_id == "T1003.001":
        mitre_tech_name = "LSASS Memory Dump"
        
    severity_breakdown = {
        "anomaly_score": alert.anomaly_score,
        "intel_match_score": alert.intel_match_score,
        "tactic_weight": alert.tactic_weight,
        "asset_criticality": alert.asset_criticality
    }
    
    notes_response = []
    for note in notes:
        # Load user display info
        author_result = await db.execute(select(User).where(User.id == note.user_id))
        author = author_result.scalars().first()
        notes_response.append({
            "id": note.id,
            "alert_id": note.alert_id,
            "user": {"id": author.id, "full_name": author.full_name} if author else None,
            "content": note.content,
            "created_at": note.created_at
        })
    
    alert_detail = {
        "id": alert.id,
        "title": alert.title,
        "severity": alert.severity,
        "severity_score": alert.severity_score,
        "severity_breakdown": severity_breakdown,
        "source_ip": alert.source_ip,
        "dest_ip": alert.dest_ip,
        "source_port": None,  # Will be mapped from first event details if needed
        "dest_port": None,
        "event_type": alert.event_type,
        "bytes_transferred": None,
        "mitre_tactic": alert.mitre_tactic,
        "mitre_technique_id": alert.mitre_technique_id,
        "mitre_technique_name": mitre_tech_name,
        "mitre_confidence": alert.mitre_confidence,
        "mitre_url": f"https://attack.mitre.org/techniques/{alert.mitre_technique_id.split('.')[0]}" if alert.mitre_technique_id else None,
        "status": alert.status,
        "event_count": alert.event_count,
        "first_seen_at": alert.first_seen_at,
        "last_seen_at": alert.last_seen_at,
        "created_at": alert.created_at,
        "notes": notes_response,
        "explanation": None  # Triggered lazily on client request
    }
    
    # Map first event ports and bytes if events exist
    if related_events:
        first_ev = related_events[0]
        alert_detail["source_port"] = first_ev.source_port
        alert_detail["dest_port"] = first_ev.dest_port
        alert_detail["bytes_transferred"] = first_ev.bytes_transferred
        
    return {
        "alert": alert_detail,
        "related_events": related_events
    }

@router.get("/{alert_id}/explanation")
async def get_alert_explanation(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves or generates the AI RAG summary for this alert, returning fallback values if LLM fails."""
    query = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(query)
    alert = result.scalars().first()
    
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
        
    explanation = await get_or_generate_explanation(alert, db)
    return explanation

@router.patch("/{alert_id}/action")
async def action_alert(
    alert_id: uuid.UUID,
    action_data: AlertActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(query)
    alert = result.scalars().first()
    
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
        
    # Check if already resolved / actioned
    if alert.status in ["escalated", "dismissed", "false_positive", "resolved"]:
        # Retrieve actioner's name
        actioner_name = "Another analyst"
        if alert.actioned_by:
            act_res = await db.execute(select(User).where(User.id == alert.actioned_by))
            act_user = act_res.scalars().first()
            if act_user:
                actioner_name = act_user.full_name
                
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "ALERT_ALREADY_ACTIONED",
                "message": f"This alert was already {alert.status} by {actioner_name}.",
                "detail": {
                    "current_status": alert.status,
                    "actioned_by": actioner_name,
                    "actioned_at": alert.actioned_at.isoformat() if alert.actioned_at else None
                }
            }
        )

    # Perform action mapping
    target_status = "open"
    if action_data.action == "escalate":
        if not action_data.assignee_id:
            raise HTTPException(status_code=422, detail="assignee_id is required for escalation.")
        target_status = "escalated"
        alert.escalated_to = action_data.assignee_id
    elif action_data.action == "dismiss":
        target_status = "dismissed"
    elif action_data.action == "false_positive":
        target_status = "false_positive"
        # Save false positive feedback entry
        fb = AnalystFeedback(
            id=uuid.uuid4(),
            alert_id=alert.id,
            user_id=current_user.id,
            feedback_type="false_positive",
            fp_reason=action_data.priority or "other",  # Map fields
            notes=action_data.note,
            alert_signature=alert.alert_signature
        )
        db.add(fb)
    elif action_data.action == "resolve":
        target_status = "resolved"
    else:
        raise HTTPException(status_code=422, detail="Invalid action value.")

    # Update alert parameters
    alert.status = target_status
    alert.actioned_by = current_user.id
    alert.actioned_at = datetime.utcnow()
    alert.updated_at = datetime.utcnow()
    
    # Save accompanying note if provided
    if action_data.note:
        note_text = action_data.note
        if action_data.action == "escalate":
            note_text = f"[Escalated {action_data.priority or 'P1'}] {note_text}"
        db_note = AnalystNote(
            id=uuid.uuid4(),
            alert_id=alert.id,
            user_id=current_user.id,
            content=note_text
        )
        db.add(db_note)

    await db.commit()
    
    # Broadcast alert updates to dashboard streams
    await queue_hub.broadcast_alert({
        "event": "alert_updated",
        "data": {
            "id": str(alert.id),
            "status": alert.status,
            "actioned_by": current_user.full_name,
            "actioned_at": alert.actioned_at.isoformat()
        }
    })
    
    return {
        "alert_id": alert.id,
        "status": alert.status,
        "actioned_by": current_user.id,
        "actioned_at": alert.actioned_at
    }

@router.post("/{alert_id}/notes", status_code=status.HTTP_201_CREATED, response_model=NoteResponse)
async def add_alert_note(
    alert_id: uuid.UUID,
    note_data: NoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Alert).where(Alert.id == alert_id)
    result = await db.execute(query)
    alert = result.scalars().first()
    
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
        
    db_note = AnalystNote(
        id=uuid.uuid4(),
        alert_id=alert_id,
        user_id=current_user.id,
        content=note_data.content
    )
    db.add(db_note)
    await db.commit()
    
    return {
        "id": db_note.id,
        "alert_id": db_note.alert_id,
        "user": {"id": current_user.id, "full_name": current_user.full_name},
        "content": db_note.content,
        "created_at": db_note.created_at
    }
