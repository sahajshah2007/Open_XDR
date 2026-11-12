"""Bridge ACDT's Falco and lab events into the shared OpenXDR event schema."""
from acdt.telemetry.normalizer import normalize
from acdt.detection.attack_map import techniques_for
from app.schemas.event import NormalizedEvent
from app.services.parsers.common import utc_timestamp


def parse_acdt(source, raw):
    original = normalize(source, raw)
    fields = raw.get("output_fields", {})
    techniques = techniques_for(original)
    priority = str(raw.get("priority", "medium")).lower()
    severity = {"emergency": "critical", "alert": "critical", "error": "high", "warning": "medium", "notice": "low", "debug": "informational"}.get(priority, priority)
    if severity not in {"critical", "high", "medium", "low", "informational"}:
        severity = "medium"
    host = raw.get("hostname") or raw.get("host") or raw.get("target")
    return NormalizedEvent(
        timestamp=utc_timestamp(original.timestamp), source=source,
        event_type=original.event_type, src_ip=original.src_ip or fields.get("fd.cip"),
        dst_ip=(original.dst_ip or fields.get("fd.sip")) if source != "attacker" else None,
        host_id=str(host) if host else None, host_name=host,
        user=fields.get("user.name") or raw.get("user"),
        process_name=fields.get("proc.exepath") or fields.get("proc.name"),
        command_line=fields.get("proc.cmdline"), severity=severity,
        product="linux" if source == "falco" else "attacker", service=source,
        category="process_creation" if fields.get("proc.name") else None,
        techniques=techniques, mitre_technique=techniques[0] if techniques else None,
        raw=raw,
    )
