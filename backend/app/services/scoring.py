from typing import List
from app.models.alert import Alert

SEVERITY_MAPPING = {
    "critical": 80,
    "high": 50,
    "medium": 25,
    "low": 10,
    "informational": 1
}

def calculate_incident_risk(alerts: List[Alert], criticality: int = 1) -> dict:
    """
    Calculates the severity and confidence score of an incident based on its alerts.
    Returns a dict with 'severity' and 'confidence'.
    """
    if not alerts:
        return {"severity": "low", "confidence": 0}
        
    base_score = 0
    max_severity_val = 0
    max_severity_str = "low"
    
    # 1. Base Score calculation (max severity)
    for alert in alerts:
        # Some rules might have numerical severity strings like "7", map them if needed
        # Assuming typical sigma levels for now
        sev = str(alert.severity).lower()
        val = SEVERITY_MAPPING.get(sev, 10)
        
        # Simple heuristic to map numerical wazuh severities
        if sev.isdigit():
            val = int(sev) * 6
            if val > 80: sev = "critical"
            elif val >= 50: sev = "high"
            elif val >= 25: sev = "medium"
            else: sev = "low"
            
        if val > max_severity_val:
            max_severity_val = val
            max_severity_str = sev
            
    base_score = max_severity_val
    base_score += max(0, min(10, criticality) - 1) * 2
    
    # 2. Modifiers
    # Multiple alerts increase the score slightly
    num_alerts = len(alerts)
    if num_alerts > 1:
        base_score += min(20, num_alerts * 2)
        
    # Multi-source correlation boosts confidence heavily
    sources = set(alert.source for alert in alerts if getattr(alert, "source", None))
    if len(sources) > 1:
        base_score += 30

    tactics = set(alert.mitre_tactic for alert in alerts if alert.mitre_tactic)
    if len(tactics) > 1:
        base_score += 25
        
    # Cap at 100
    confidence = min(100, base_score)
    
    # Recalculate severity string based on final confidence if it escalated
    if confidence >= 80: final_severity = "critical"
    elif confidence >= 50: final_severity = "high"
    elif confidence >= 25: final_severity = "medium"
    else: final_severity = "low"
    
    return {
        "severity": final_severity,
        "confidence": confidence
    }
