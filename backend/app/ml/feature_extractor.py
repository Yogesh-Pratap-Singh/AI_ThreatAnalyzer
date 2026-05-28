import ipaddress
from datetime import datetime
import numpy as np

def is_private_ip(ip_str: str) -> int:
    if not ip_str:
        return 0
    try:
        ip = ipaddress.ip_address(ip_str)
        return 1 if ip.is_private else 0
    except ValueError:
        return 0

def encode_protocol(protocol: str) -> int:
    if not protocol:
        return 0
    p = protocol.lower()
    if "tcp" in p:
        return 1
    elif "udp" in p:
        return 2
    elif "icmp" in p:
        return 3
    return 0

def extract_features(event_dict: dict) -> np.ndarray:
    """
    Extracts numerical features from a normalized event dictionary:
    [hour_of_day, bytes_transferred, dest_port, is_internal_dest, protocol_encoded, events_from_ip_last_hour]
    """
    event_time_str = event_dict.get("event_time")
    if isinstance(event_time_str, datetime):
        dt = event_time_str
    elif event_time_str:
        try:
            # Parse ISO8601
            dt = datetime.fromisoformat(event_time_str.replace("Z", "+00:00"))
        except Exception:
            dt = datetime.utcnow()
    else:
        dt = datetime.utcnow()

    hour_of_day = dt.hour
    bytes_transferred = int(event_dict.get("bytes_transferred") or 0)
    dest_port = int(event_dict.get("dest_port") or 0)
    
    dest_ip = event_dict.get("dest_ip") or ""
    is_internal_dest = is_private_ip(dest_ip)
    
    protocol = event_dict.get("protocol") or ""
    protocol_encoded = encode_protocol(protocol)
    
    # default local events_from_ip_last_hour baseline to 1 (will be updated dynamically if db is queried)
    events_from_ip_last_hour = int(event_dict.get("events_from_ip_last_hour") or 1)
    
    features = [
        hour_of_day,
        bytes_transferred,
        dest_port,
        is_internal_dest,
        protocol_encoded,
        events_from_ip_last_hour
    ]
    return np.array(features, dtype=float)
