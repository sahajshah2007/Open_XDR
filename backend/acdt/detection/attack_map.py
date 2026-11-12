"""Map telemetry events to MITRE ATT&CK techniques.

Rules pull technique IDs from event tags (Falco) or from a rule->technique
lookup table (Zeek/Wazuh/attacker events).
"""
from __future__ import annotations

from typing import List

from acdt.telemetry.normalizer import NormalizedEvent

# Minimal seed lookup: event_type / keyword -> ATT&CK technique IDs.
RULE_TO_TECHNIQUES = {
    "brute_force": ["T1110"],
    "Terminal shell in container": ["T1059"],
    "ssh": ["T1021.004"],
    "sqli": ["T1190"],
    "web_shell": ["T1505.003"],
}


def techniques_for(event: NormalizedEvent) -> List[str]:
    """Return ATT&CK technique IDs associated with an event."""
    techniques: List[str] = []

    # Falco events carry ATT&CK tags directly (e.g. "T1059").
    tags = event.payload.get("tags", []) if isinstance(event.payload, dict) else []
    techniques.extend(t for t in tags if _looks_like_technique(t))

    # Fall back to the lookup table keyed on event type.
    techniques.extend(RULE_TO_TECHNIQUES.get(event.event_type, []))

    # Deduplicate while preserving order.
    seen = set()
    result = []
    for t in techniques:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result


def _looks_like_technique(tag: str) -> bool:
    return isinstance(tag, str) and tag.startswith("T") and tag[1:2].isdigit()
