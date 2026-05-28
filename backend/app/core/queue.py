import asyncio
from typing import Set, Dict

class EventQueueHub:
    def __init__(self):
        # Point-to-point queues for event processing pipeline
        self.raw_events: asyncio.Queue = asyncio.Queue()
        self.normalized_events: asyncio.Queue = asyncio.Queue()
        self.scored_events: asyncio.Queue = asyncio.Queue()
        
        # Pub-sub SSE listeners for real-time dashboard notifications
        self.alert_listeners: Set[asyncio.Queue] = set()

    async def publish_raw(self, event_data: dict):
        await self.raw_events.put(event_data)

    async def publish_normalized(self, event_data: dict):
        await self.normalized_events.put(event_data)

    async def publish_scored(self, event_data: dict):
        await self.scored_events.put(event_data)

    async def broadcast_alert(self, alert_data: dict):
        # Broadcast alert to all active SSE streaming connections
        if self.alert_listeners:
            for listener in list(self.alert_listeners):
                try:
                    await listener.put(alert_data)
                except Exception:
                    # Remove broken listeners if they failed
                    self.alert_listeners.discard(listener)

    def register_alert_listener(self) -> asyncio.Queue:
        listener = asyncio.Queue()
        self.alert_listeners.add(listener)
        return listener

    def unregister_alert_listener(self, listener: asyncio.Queue):
        self.alert_listeners.discard(listener)

# Global broker instance
queue_hub = EventQueueHub()
