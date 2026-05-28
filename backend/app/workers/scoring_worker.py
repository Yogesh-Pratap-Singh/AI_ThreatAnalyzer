import asyncio
import logging
import uuid
from datetime import datetime
from sqlalchemy.future import select
from app.core.queue import queue_hub
from app.ml.feature_extractor import extract_features
from app.ml.anomaly_detector import detector
from app.db.session import SessionLocal
from app.models.all_models import Event

logger = logging.getLogger("scoring_worker")

async def get_recent_event_count_from_db(source_ip: str) -> int:
    """Helper to query DB for recent event count from source IP (last 1 hour)."""
    if not source_ip:
        return 1
    async with SessionLocal() as db:
        try:
            # Simple count query over the last hour
            query = f"SELECT count(*) FROM events WHERE source_ip = :ip AND event_time > now() - interval '1 hour';"
            result = await db.execute(query, {"ip": source_ip})
            count = result.scalar() or 0
            return count + 1
        except Exception:
            return 1

async def start_scoring_worker():
    logger.info("Starting Anomaly Scoring Worker...")
    while True:
        try:
            normalized_event = await queue_hub.normalized_events.get()
            
            source_ip = normalized_event.get("source_ip")
            
            # Fetch events from IP in the last hour dynamically
            recent_count = await get_recent_event_count_from_db(source_ip)
            normalized_event["events_from_ip_last_hour"] = recent_count
            
            # Extract features and compute anomaly score
            features = extract_features(normalized_event)
            score = detector.score_event(features)
            
            scored_event = {**normalized_event, "anomaly_score": score}
            
            # If anomaly score is above 0.5, store to PostgreSQL database
            if score > 0.5:
                async with SessionLocal() as db:
                    event_obj = Event(
                        id=uuid.uuid4(),
                        source_id=uuid.UUID(scored_event["source_id"]) if isinstance(scored_event["source_id"], str) else scored_event["source_id"],
                        event_time=datetime.fromisoformat(scored_event["event_time"].replace("Z", "+00:00")),
                        source_ip=scored_event["source_ip"],
                        dest_ip=scored_event["dest_ip"],
                        source_port=scored_event["source_port"],
                        dest_port=scored_event["dest_port"],
                        protocol=scored_event["protocol"],
                        event_type=scored_event["event_type"],
                        bytes_transferred=scored_event["bytes_transferred"],
                        anomaly_score=score,
                        raw_payload=scored_event["raw_payload"]
                    )
                    db.add(event_obj)
                    await db.commit()
                    # Store database ID back into dict for referencing
                    scored_event["id"] = event_obj.id

            await queue_hub.publish_scored(scored_event)
            queue_hub.normalized_events.task_done()
        except asyncio.CancelledError:
            logger.info("Anomaly Scoring Worker stopped.")
            break
        except Exception as e:
            logger.error(f"Error in Anomaly Scoring Worker: {e}", exc_info=True)
            await asyncio.sleep(1)
