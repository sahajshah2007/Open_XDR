from app.models.incident import Incident
from app.models.alert import Alert
from app.services.parsers.common import utc_timestamp

def analyze_incident_behavior(incident: Incident, alerts: list[Alert]):
    """
    UEBA (User and Entity Behavior Analytics) Engine
    Checks temporal and behavioral patterns within an incident to override base math scores.
    """
    
    tactics = set()
    for alert in alerts:
        if alert.mitre_tactic:
            tactics.add(alert.mitre_tactic.lower())
            
    # Pattern 1: Initial Access -> Exfiltration (Smash and Grab)
    # If an attacker gains initial access and immediately exfiltrates data, escalate to CRITICAL.
    if "initial-access" in tactics and "exfiltration" in tactics:
        # Check time window (e.g. less than 24 hours between them)
        initial_access_alerts = [a for a in alerts if a.mitre_tactic and a.mitre_tactic.lower() == "initial-access"]
        exfiltration_alerts = [a for a in alerts if a.mitre_tactic and a.mitre_tactic.lower() == "exfiltration"]
        
        if initial_access_alerts and exfiltration_alerts:
            # Find the earliest initial access
            earliest_access = min([utc_timestamp(a.timestamp) for a in initial_access_alerts])
            # Find the earliest exfiltration
            earliest_exfil = min([utc_timestamp(a.timestamp) for a in exfiltration_alerts])
            
            # If exfiltration happened AFTER initial access, within 24 hours
            if earliest_access < earliest_exfil and (earliest_exfil - earliest_access).total_seconds() < 86400:
                incident.severity = "critical"
                incident.confidence = 100
                incident.title = f"CRITICAL: Smash and Grab (Initial Access -> Exfiltration)"
                return
                
    # Pattern 2: Discovery -> Credential Access -> Lateral Movement
    if "discovery" in tactics and "credential-access" in tactics and "lateral-movement" in tactics:
        incident.severity = "critical"
        incident.confidence = 95
        incident.title = f"CRITICAL: Lateral Movement Kill-chain Detected"
        return
