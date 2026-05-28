import httpx
import uuid
import json
from datetime import datetime

# API settings
INGEST_URL = "http://localhost:8000/api/v1/ingest/events"
SOURCE_ID = "8b9b8b20-df5b-4395-8e31-862d66579b29"  # Seeded Network Firewall Logs
API_KEY = "dev-api-key-12345"

headers = {
    "X-Source-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def send_events(events):
    payload = {
        "source_id": SOURCE_ID,
        "events": events
    }
    
    print(f"Sending ingestion payload containing {len(events)} events...")
    try:
        response = httpx.post(INGEST_URL, json=payload, headers=headers)
        print(f"Response status code: {response.status_code}")
        print(f"Response JSON: {response.json()}")
    except Exception as e:
        print(f"Failed to connect to ingestion server: {e}")

if __name__ == "__main__":
    # 1. Normal Event: Standard HTTPS traffic during the day (14:30), small bytes (4096)
    normal_event = {
        "timestamp": datetime(2026, 5, 28, 14, 30, 0).isoformat(),
        "source_ip": "192.168.1.15",
        "dest_ip": "8.8.8.8",
        "source_port": 50123,
        "dest_port": 443,
        "protocol": "TCP",
        "event_type": "network_connection",
        "bytes": 4096,
        "raw": {"log_message": "Session established successfully"}
    }

    # 2. Anomalous Event: Suspicious data transfer at 3:15 AM on non-standard port (8043), massive bytes (75MB)
    anomalous_event = {
        "timestamp": datetime(2026, 5, 28, 3, 15, 0).isoformat(),
        "source_ip": "192.168.1.159",
        "dest_ip": "198.51.100.42",
        "source_port": 49152,
        "dest_port": 8043,
        "protocol": "TCP",
        "event_type": "data_exfiltration", # contains "exfil" keyword which maps to Exfiltration tactic
        "bytes": 78643200, # 75 MB
        "raw": {"alert_reason": "Outbound connection to unclassified external IP with high transfer volume"}
    }

    print("--- Simulating Normal Event Ingestion ---")
    send_events([normal_event])

    print("\n--- Simulating Anomalous Event Ingestion ---")
    send_events([anomalous_event])
