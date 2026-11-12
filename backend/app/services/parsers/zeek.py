from typing import Any, Dict
from datetime import datetime
from app.schemas.event import NormalizedEvent
from app.services.parsers.common import utc_timestamp

def parse_zeek(raw_data: Dict[str, Any]) -> NormalizedEvent:
    service = raw_data.get("service", "unknown_service")
    
    # Zeek uses Unix epoch for 'ts'
    ts = raw_data.get("ts")
    timestamp = utc_timestamp(ts)

    return NormalizedEvent(
        timestamp=timestamp,
        source="zeek",
        event_type=f"zeek_conn_{service}",
        severity="informational",
        src_ip=raw_data.get("id.orig_h"),
        dst_ip=raw_data.get("id.resp_h"),
        product="zeek",
        service=raw_data.get("_path", "conn"),
        raw=raw_data
    )
