import asyncio
import logging
from datetime import datetime
from app.core.queue import queue_hub

logger = logging.getLogger("normalization_worker")

async def normalize_event(raw_event: dict) -> dict:
    """Normalizes raw input event dictionary into a unified schema format."""
    # Parse event time
    event_time = raw_event.get("timestamp") or raw_event.get("event_time")
    if not event_time:
        event_time = datetime.utcnow().isoformat()
    elif isinstance(event_time, datetime):
        event_time = event_time.isoformat()

    # Extract bytes
    bytes_transferred = raw_event.get("bytes") or raw_event.get("bytes_transferred")
    if bytes_transferred is not None:
        try:
            bytes_transferred = int(bytes_transferred)
        except ValueError:
            bytes_transferred = 0
            
    # Extract ports
    s_port = raw_event.get("source_port")
    d_port = raw_event.get("dest_port")
    source_port = int(s_port) if s_port is not None else None
    dest_port = int(d_port) if d_port is not None else None

    normalized = {
        "source_id": raw_event.get("source_id"),
        "event_time": event_time,
        "source_ip": raw_event.get("source_ip"),
        "dest_ip": raw_event.get("dest_ip"),
        "source_port": source_port,
        "dest_port": dest_port,
        "protocol": raw_event.get("protocol"),
        "event_type": raw_event.get("event_type") or "network_connection",
        "bytes_transferred": bytes_transferred,
        "raw_payload": raw_event.get("raw") or raw_event
    }
    return normalized

async def start_normalization_worker():
    logger.info("Starting Normalization Worker...")
    while True:
        try:
            raw_event = await queue_hub.raw_events.get()
            normalized = await normalize_event(raw_event)
            await queue_hub.publish_normalized(normalized)
            queue_hub.raw_events.task_done()
        except asyncio.CancelledError:
            logger.info("Normalization Worker stopped.")
            break
        except Exception as e:
            logger.error(f"Error in Normalization Worker: {e}", exc_info=True)
            await asyncio.sleep(1)
