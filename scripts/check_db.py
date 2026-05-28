import os
import sys
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.session import SessionLocal
from sqlalchemy.future import select
from app.models.all_models import Event, Alert

async def main():
    async with SessionLocal() as db:
        # Check events
        result_events = await db.execute(select(Event))
        events = result_events.scalars().all()
        print(f"--- Database Events Count: {len(events)} ---")
        for ev in events:
            print(f"ID: {ev.id} | IP: {ev.source_ip} | Type: {ev.event_type} | Bytes: {ev.bytes_transferred} | Score: {ev.anomaly_score}")
            
        # Check alerts
        result_alerts = await db.execute(select(Alert))
        alerts = result_alerts.scalars().all()
        print(f"\n--- Database Alerts Count: {len(alerts)} ---")
        for al in alerts:
            print(f"ID: {al.id} | Title: {al.title} | Severity: {al.severity} | Score: {al.severity_score} | Tactic: {al.mitre_tactic} | Status: {al.status}")

if __name__ == "__main__":
    asyncio.run(main())
