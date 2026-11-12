from typing import Any, Dict
from datetime import datetime
from app.schemas.event import NormalizedEvent
from app.services.parsers.common import utc_timestamp

def parse_suricata(raw_data: Dict[str, Any]) -> NormalizedEvent:
    alert = raw_data.get("alert", {})
    
    # Optional fields
    timestamp_str = raw_data.get("timestamp")
    timestamp = utc_timestamp(timestamp_str)

    # Determine severity (Suricata uses 1-4 usually, lower is worse)
    # We can map it roughly to our 1-10 scale or string scale if needed,
    # but for now we pass it as a string
    raw_sev = alert.get("severity", 3)
    sev_str = str(raw_sev)
    
    if raw_sev == 1: sev_str = "high"
    elif raw_sev == 2: sev_str = "medium"
    else: sev_str = "low"

    return NormalizedEvent(
        timestamp=timestamp,
        source="suricata",
        event_type=alert.get("signature", "unknown_suricata_alert"),
        severity=sev_str,
        src_ip=raw_data.get("src_ip"),
        dst_ip=raw_data.get("dest_ip"),
        product="suricata",
        service=raw_data.get("event_type", "alert"),
        # We don't typically have host_id for network traffic unless mapped
        raw=raw_data
    )
