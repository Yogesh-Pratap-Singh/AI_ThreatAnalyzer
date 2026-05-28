import asyncio
import logging
import uuid
import hashlib
from datetime import datetime
from sqlalchemy.future import select
from app.core.config import settings
from app.core.queue import queue_hub
from app.db.session import SessionLocal
from app.models.all_models import Alert, Event, alert_events
from app.services.severity_service import compute_severity_score, score_to_severity, get_tactic_weight

logger = logging.getLogger("alert_worker")

def get_alert_signature(source_ip: str, event_type: str, dest_port: int, day_str: str) -> str:
    """Computes a unique SHA-256 signature for alert deduplication."""
    sig_input = f"{source_ip or ''}:{event_type or ''}:{dest_port or 0}:{day_str}"
    return hashlib.sha256(sig_input.encode("utf-8")).hexdigest()

def guess_mitre_tactic(event_type: str) -> tuple:
    """Provides a baseline keyword-based mapping to a MITRE tactic and technique."""
    et = (event_type or "").lower()
    if "exfil" in et or "outbound" in et:
        return "Exfiltration", "T1048", "Exfiltration Over Alternative Protocol"
    elif "c2" in et or "beacon" in et or "tor" in et or "command" in et:
        return "Command and Control", "T1071", "Application Layer Protocol"
    elif "lateral" in et:
        return "Lateral Movement", "T1021", "Remote Services"
    elif "priv" in et or "escalat" in et:
        return "Privilege Escalation", "T1068", "Exploitation for Privilege Escalation"
    elif "persist" in et:
        return "Persistence", "T1098", "Account Manipulation"
    elif "cred" in et or "login_fail" in et:
        return "Credential Access", "T1003", "OS Credential Dumping"
    elif "evas" in et or "bypass" in et:
        return "Defense Evasion", "T1036", "Masquerading"
    elif "disc" in et or "scan" in et:
        return "Discovery", "T1082", "System Information Discovery"
    elif "recon" in et:
        return "Reconnaissance", "T1595", "Active Scanning"
    elif "exec" in et:
        return "Execution", "T1203", "Exploitation for Client Execution"
    elif "collect" in et:
        return "Collection", "T1114", "Email Collection"
    elif "impact" in et or "dos" in et or "wipe" in et:
        return "Impact", "T1485", "Data Destruction"
    return "Initial Access", "T1190", "Exploitation of Public-Facing Application"

async def start_alert_worker():
    logger.info("Starting Alert Generation Worker...")
    while True:
        try:
            scored_event = await queue_hub.scored_events.get()
            score = scored_event["anomaly_score"]
            
            # Filter events by Anomaly Threshold
            if score >= settings.ANOMALY_THRESHOLD:
                event_time_str = scored_event["event_time"]
                event_time = datetime.fromisoformat(event_time_str.replace("Z", "+00:00"))
                day_str = event_time.strftime("%Y-%m-%d")
                
                source_ip = scored_event.get("source_ip")
                event_type = scored_event.get("event_type") or "network_connection"
                dest_port = scored_event.get("dest_port") or 0
                event_id = scored_event.get("id")
                
                # Compute daily deduplication signature
                sig = get_alert_signature(source_ip, event_type, dest_port, day_str)
                
                async with SessionLocal() as db:
                    # Check for an existing open alert with this signature
                    query = select(Alert).where(Alert.alert_signature == sig, Alert.status == "open")
                    result = await db.execute(query)
                    alert = result.scalars().first()
                    
                    if alert:
                        # Deduplication: Update existing alert
                        alert.event_count += 1
                        alert.last_seen_at = max(alert.last_seen_at, event_time)
                        alert.updated_at = datetime.utcnow()
                        
                        # Link event to alert if event was persisted
                        if event_id:
                            await db.execute(alert_events.insert().values(alert_id=alert.id, event_id=event_id))
                        
                        await db.commit()
                        logger.info(f"Deduplicated event to existing alert: {alert.id}")
                        
                        # Broadcast update to connected SSE streams
                        await queue_hub.broadcast_alert({
                            "event": "alert_updated",
                            "data": {
                                "id": str(alert.id),
                                "status": alert.status,
                                "event_count": alert.event_count,
                                "last_seen_at": alert.last_seen_at.isoformat()
                            }
                        })
                    else:
                        # Correlate and create a new Alert
                        mitre_tactic, mitre_tech_id, mitre_tech_name = guess_mitre_tactic(event_type)
                        tactic_weight = get_tactic_weight(mitre_tactic)
                        
                        # Composite severity scoring formula
                        severity_score = compute_severity_score(
                            anomaly_score=score,
                            intel_match_score=0.0,  # Seeded baseline
                            tactic_weight=tactic_weight,
                            asset_criticality=0.5   # Default importance
                        )
                        severity = score_to_severity(severity_score)
                        
                        new_alert = Alert(
                            id=uuid.uuid4(),
                            title=f"Unusual {event_type.replace('_', ' ')} activity from {source_ip}",
                            severity=severity,
                            severity_score=severity_score,
                            anomaly_score=score,
                            intel_match_score=0.0,
                            tactic_weight=tactic_weight,
                            asset_criticality=0.5,
                            source_ip=source_ip,
                            dest_ip=scored_event.get("dest_ip"),
                            event_type=event_type,
                            mitre_tactic=mitre_tactic,
                            mitre_technique_id=mitre_tech_id,
                            mitre_confidence=0.85,
                            alert_signature=sig,
                            status="open",
                            event_count=1,
                            first_seen_at=event_time,
                            last_seen_at=event_time
                        )
                        
                        db.add(new_alert)
                        await db.flush()  # Allocate alert.id in session
                        
                        if event_id:
                            await db.execute(alert_events.insert().values(alert_id=new_alert.id, event_id=event_id))
                        
                        await db.commit()
                        logger.info(f"Created new alert: {new_alert.id}")
                        
                        # Broadcast new alert to connected SSE streams
                        await queue_hub.broadcast_alert({
                            "event": "new_alert",
                            "data": {
                                "id": str(new_alert.id),
                                "title": new_alert.title,
                                "severity": new_alert.severity,
                                "severity_score": new_alert.severity_score,
                                "source_ip": new_alert.source_ip,
                                "dest_ip": new_alert.dest_ip,
                                "event_type": new_alert.event_type,
                                "mitre_tactic": new_alert.mitre_tactic,
                                "mitre_technique_id": new_alert.mitre_technique_id,
                                "status": new_alert.status,
                                "event_count": new_alert.event_count,
                                "first_seen_at": new_alert.first_seen_at.isoformat(),
                                "last_seen_at": new_alert.last_seen_at.isoformat(),
                                "created_at": new_alert.created_at.isoformat()
                            }
                        })
            
            queue_hub.scored_events.task_done()
        except asyncio.CancelledError:
            logger.info("Alert Worker stopped.")
            break
        except Exception as e:
            logger.error(f"Error in Alert Worker: {e}", exc_info=True)
            await asyncio.sleep(1)
