"""Preserve detections already made by upstream security tools."""
from app.services.parsers.common import tactic_name


def detections_for(event, *, enabled_sources=None, wazuh_min_level=3):
    if enabled_sources is not None and event.source not in enabled_sources:
        return []
    raw = event.raw
    if event.source == "wazuh" and raw.get("rule", {}).get("id"):
        rule = raw["rule"]
        level = int(rule.get("level", 0))
        if level < wazuh_min_level:
            return []
        severity = "critical" if level >= 12 else "high" if level >= 8 else "medium" if level >= 5 else "low"
        return [{"id": f"wazuh:{rule['id']}", "title": event.event_type,
                 "level": severity, "tags": []}]
    if event.source == "suricata" and raw.get("alert", {}).get("signature_id"):
        return [{"id": f"suricata:{raw['alert']['signature_id']}", "title": event.event_type,
                 "level": event.severity or "medium", "tags": []}]
    if event.source == "falco" and raw.get("rule"):
        return [{"id": f"falco:{event.event_type}", "title": event.event_type,
                 "level": event.severity or "medium", "tags": raw.get("tags", [])}]
    # Lab signals are explicitly labeled; ordinary Zeek connections are telemetry.
    if event.source == "attacker" and event.techniques:
        return [{"id": f"simulation:{event.event_type}", "title": f"Simulation: {event.event_type}",
                 "level": "medium", "tags": []}]
    return []
