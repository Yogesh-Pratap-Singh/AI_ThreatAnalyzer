from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, case

from app.core.deps import get_db, get_current_user
from app.models.all_models import Alert, User
from app.schemas.all_schemas import ReportResponse

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/summary", response_model=ReportResponse)
async def get_summary_report(
    from_time: datetime = Query(...),
    to_time: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if from_time > to_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_time must be before to_time"
        )

    # 1. Total alerts in range
    total_query = select(func.count(Alert.id)).where(
        and_(Alert.created_at >= from_time, Alert.created_at <= to_time)
    )
    total_res = await db.execute(total_query)
    total_alerts = total_res.scalar() or 0

    if total_alerts == 0:
        return {
            "period": {"from": from_time, "to": to_time},
            "total_alerts": 0,
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "false_positive_rate": 0.0,
            "mean_triage_time_minutes": 0,
            "top_mitre_tactics": [],
            "top_source_ips": [],
            "alert_volume_by_day": []
        }

    # 2. By Severity
    sev_query = (
        select(Alert.severity, func.count(Alert.id))
        .where(and_(Alert.created_at >= from_time, Alert.created_at <= to_time))
        .group_by(Alert.severity)
    )
    sev_res = await db.execute(sev_query)
    by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for row in sev_res.all():
        sev, cnt = row
        if sev in by_severity:
            by_severity[sev] = cnt

    # 3. False Positive Rate
    # Rate = dismissed or false_positive status / total
    fp_query = select(func.count(Alert.id)).where(
        and_(
            Alert.created_at >= from_time,
            Alert.created_at <= to_time,
            Alert.status.in_(["dismissed", "false_positive"])
        )
    )
    fp_res = await db.execute(fp_query)
    fp_count = fp_res.scalar() or 0
    false_positive_rate = round(fp_count / total_alerts, 4)

    # 4. Mean Triage Time in Minutes
    # Average of (actioned_at - created_at)
    # Using epoch extraction for platform portability
    mttt_query = select(
        func.avg(
            (func.extract("epoch", Alert.actioned_at) - func.extract("epoch", Alert.created_at)) / 60.0
        )
    ).where(
        and_(
            Alert.created_at >= from_time,
            Alert.created_at <= to_time,
            Alert.actioned_at.isnot(None)
        )
    )
    mttt_res = await db.execute(mttt_query)
    mttt_avg = mttt_res.scalar()
    mean_triage_time_minutes = int(round(mttt_avg)) if mttt_avg is not None else 0

    # 5. Top MITRE Tactics
    tactic_query = (
        select(Alert.mitre_tactic, func.count(Alert.id))
        .where(
            and_(
                Alert.created_at >= from_time,
                Alert.created_at <= to_time,
                Alert.mitre_tactic.isnot(None)
            )
        )
        .group_by(Alert.mitre_tactic)
        .order_by(func.count(Alert.id).desc())
        .limit(5)
    )
    tactic_res = await db.execute(tactic_query)
    top_mitre_tactics = [
        {"tactic": row[0], "count": row[1]} for row in tactic_res.all()
    ]

    # 6. Top Source IPs
    ip_query = (
        select(Alert.source_ip, func.count(Alert.id))
        .where(
            and_(
                Alert.created_at >= from_time,
                Alert.created_at <= to_time,
                Alert.source_ip.isnot(None)
            )
        )
        .group_by(Alert.source_ip)
        .order_by(func.count(Alert.id).desc())
        .limit(5)
    )
    ip_res = await db.execute(ip_query)
    top_source_ips = [
        {"ip": row[0], "alert_count": row[1]} for row in ip_res.all()
    ]

    # 7. Alert Volume by Day
    # Group by date of created_at
    day_query = (
        select(
            func.to_char(Alert.created_at, "YYYY-MM-DD").label("day"),
            func.count(Alert.id)
        )
        .where(and_(Alert.created_at >= from_time, Alert.created_at <= to_time))
        .group_by("day")
        .order_by("day")
    )
    day_res = await db.execute(day_query)
    alert_volume_by_day = [
        {"date": row[0], "count": row[1]} for row in day_res.all()
    ]

    return {
        "period": {"from": from_time, "to": to_time},
        "total_alerts": total_alerts,
        "by_severity": by_severity,
        "false_positive_rate": false_positive_rate,
        "mean_triage_time_minutes": mean_triage_time_minutes,
        "top_mitre_tactics": top_mitre_tactics,
        "top_source_ips": top_source_ips,
        "alert_volume_by_day": alert_volume_by_day
    }
