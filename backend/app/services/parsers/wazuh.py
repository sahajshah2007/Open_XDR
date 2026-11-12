from typing import Any, Dict
from datetime import datetime
from app.schemas.event import NormalizedEvent
from app.services.parsers.common import utc_timestamp, tactic_name

def parse_wazuh(raw_data: Dict[str, Any]) -> NormalizedEvent:
    rule = raw_data.get("rule", {})
    agent = raw_data.get("agent", {})
    data_block = raw_data.get("data", {})
    
    # Extract MITRE data
    mitre_block = rule.get("mitre", {})
    tactics = mitre_block.get("tactic", [])
    techniques = mitre_block.get("id", [])
    
    mitre_tactic = tactic_name(tactics[0]) if tactics else None
    mitre_technique = techniques[0] if techniques else None
    
    # Optional fields
    timestamp_str = raw_data.get("timestamp")
    timestamp = utc_timestamp(timestamp_str)
    process = data_block.get("win", {}).get("eventdata", {}).get("image") or data_block.get("process_name") or data_block.get("Image")

    return NormalizedEvent(
        timestamp=timestamp,
        source="wazuh",
        event_type=rule.get("description", "unknown_wazuh_event"),
        severity=str(rule.get("level", "0")),
        host_name=agent.get("name"),
        host_id=agent.get("id"),
        src_ip=data_block.get("srcip"),
        dst_ip=data_block.get("dstip"),
        user=data_block.get("user") or data_block.get("dstuser") or data_block.get("srcuser"),
        process_name=data_block.get("win", {}).get("eventdata", {}).get("image") or data_block.get("process_name") or data_block.get("Image"),
        command_line=data_block.get("win", {}).get("eventdata", {}).get("commandLine") or data_block.get("command") or data_block.get("CommandLine"),
        mitre_tactic=mitre_tactic,
        mitre_technique=mitre_technique,
        techniques=techniques,
        product="windows" if data_block.get("win") else ("linux" if process and process.startswith("/") else "wazuh"),
        category="process_creation" if process else None,
        service=raw_data.get("decoder", {}).get("name"),
        raw=raw_data
    )
