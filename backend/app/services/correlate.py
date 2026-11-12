"""Attach alerts to persistent incidents using bounded event-time windows."""
from datetime import timedelta
from sqlalchemy import or_, text
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.host import Host
from app.services.scoring import calculate_incident_risk
from app.services.parsers.common import utc_timestamp

CORRELATION_WINDOW_MINUTES = 60


def correlate_alert(db, new_alert):
    timestamp = utc_timestamp(new_alert.timestamp)
    lower = timestamp - timedelta(minutes=CORRELATION_WINDOW_MINUTES)
    upper = timestamp + timedelta(minutes=CORRELATION_WINDOW_MINUTES)
    if db.bind.dialect.name == "postgresql":
        entity = str(new_alert.host_id or (new_alert.source_ip, new_alert.destination_ip))
        db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:entity))"), {"entity": entity})
    query = db.query(Incident).filter(Incident.status.in_(["open", "triage"]),
                                     Incident.last_seen >= lower, Incident.first_seen <= upper)
    run_id = (new_alert.raw_event or {}).get("_lab",{}).get("run_id")
    scope = Alert.raw_event["_lab"]["run_id"].as_string()
    scope_filter = scope == run_id if run_id else scope.is_(None)
    query = query.filter(Incident.alerts.any(scope_filter))
    incident = None
    if new_alert.host_id:
        incident = query.filter(Incident.host_id == new_alert.host_id).with_for_update().first()
    if incident is None and new_alert.source_ip:
        # Matching an arbitrary shared destination (e.g. a DNS resolver) is not
        # enough. Require the same source, compatible destination and event time.
        match = db.query(Alert).join(Incident).filter(
            Incident.status.in_(["open", "triage"]), Alert.timestamp >= lower,
            Alert.timestamp <= upper, Alert.source_ip == new_alert.source_ip, scope_filter)
        if new_alert.host_id:
            match = match.filter(or_(Alert.host_id == new_alert.host_id, Alert.host_id.is_(None)))
        if new_alert.destination_ip:
            match = match.filter(or_(Alert.destination_ip == new_alert.destination_ip, Alert.destination_ip.is_(None)))
        previous = match.first()
        if previous:
            incident = query.filter(Incident.incident_id == previous.incident_id).with_for_update().first()
    if incident is None:
        host = db.get(Host, new_alert.host_id) if new_alert.host_id else None
        incident = Incident(title=f"Suspicious Activity on {host.host_name}" if host else "Suspicious Network Activity",
                            host_id=new_alert.host_id, first_seen=timestamp, last_seen=timestamp,
                            severity="low", confidence=0, status="open", attack_story=[], mitre_techniques=[])
        db.add(incident)
        db.flush()
    new_alert.incident_id = incident.incident_id
    if incident.host_id is None and new_alert.host_id:
        incident.host_id = new_alert.host_id
    incident.first_seen = min(timestamp, utc_timestamp(incident.first_seen))
    incident.last_seen = max(timestamp, utc_timestamp(incident.last_seen))
    incident.attack_story = list(incident.attack_story or []) + [f"[{timestamp.isoformat()}] {new_alert.rule_name}"]
    incident.mitre_techniques = sorted(set(incident.mitre_techniques or []) | ({new_alert.mitre_technique} if new_alert.mitre_technique else set()))
    db.flush()
    alerts = db.query(Alert).filter(Alert.incident_id == incident.incident_id).all()
    host = db.get(Host, incident.host_id) if incident.host_id else None
    score = calculate_incident_risk(alerts, host.criticality if host else 1)
    incident.severity, incident.confidence = score["severity"], score["confidence"]
    from app.services.ueba import analyze_incident_behavior
    analyze_incident_behavior(incident, alerts)
    db.flush()
    return incident
