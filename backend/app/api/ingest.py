"""One ingestion contract for OpenXDR and ACDT sources."""
import logging
import secrets
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.schemas.event import RawIngestEvent
from app.models.event import Event
from app.models.host import Host
from app.models.pipeline import PipelineJob
from app.services.parsers.wazuh import parse_wazuh
from app.services.parsers.suricata import parse_suricata
from app.services.parsers.zeek import parse_zeek
from app.services.parsers.acdt import parse_acdt

logger = logging.getLogger(__name__)
router = APIRouter()
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def get_api_key(api_key: str = Security(api_key_header)):
    if api_key and secrets.compare_digest(api_key, settings.INGEST_API_KEY):
        return api_key
    raise HTTPException(status_code=403, detail="Could not validate API key")


def host_uuid_for(host_id):
    if not host_id:
        return None
    try:
        return uuid.UUID(str(host_id))
    except ValueError:
        return uuid.uuid5(uuid.NAMESPACE_DNS, str(host_id))


def normalize_event(event):
    source = event.source.lower()
    parsers = {"wazuh": parse_wazuh, "suricata": parse_suricata, "zeek": parse_zeek}
    if source in parsers:
        return parsers[source](event.data)
    if source in {"falco", "attacker"}:
        return parse_acdt(source, event.data)
    raise ValueError("Supported sources: wazuh, suricata, zeek, falco, attacker")


def persist_event(db, event, event_id=None):
    """Shared storage path for external fixtures and authenticated scenario replay."""
    try:
        normalized = normalize_event(event)
    except (ValueError, TypeError, AttributeError) as exc:
        raise HTTPException(status_code=422, detail=f"Invalid {event.source} event: {exc}") from exc
    host_id = host_uuid_for(normalized.host_id)
    if host_id:
        if normalized.host_name:
            matches = db.query(Host).filter(Host.host_name == normalized.host_name).limit(2).all()
            if len(matches) == 1:
                host_id = matches[0].host_id
        host = db.get(Host, host_id)
        if host is None:
            host = Host(host_id=host_id, host_name=normalized.host_name or normalized.host_id,
                        agent_type=normalized.source)
            db.add(host)
        host.last_seen = datetime.now(timezone.utc)
        db.flush()
        normalized.host_id = str(host_id)
    event_id = event_id or normalized.event_id
    normalized.event_id = event_id
    db.add(Event(event_id=event_id, host_id=host_id, source=normalized.source,
                 event_type=normalized.event_type, timestamp=normalized.timestamp,
                 normalized=normalized.model_dump(mode="json"), raw=event.data))
    db.flush()
    db.add(PipelineJob(event_id=event_id, twin_status="pending" if settings.NEO4J_ENABLED else "disabled"))
    db.flush()
    return db.get(Event,event_id)


@router.post("/events", status_code=202)
def ingest_event(event: RawIngestEvent, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    if "_lab" in event.data:
        raise HTTPException(status_code=422, detail="_lab metadata is reserved for authenticated experiment runs")
    stored = persist_event(db,event)
    event_id = stored.event_id
    # The event and processing intent commit together before broker dispatch.
    db.commit()
    try:
        from app.services.detection import evaluate_and_alert
        evaluate_and_alert.apply_async(args=[str(event_id)], retry=False)
    except Exception:
        logger.warning("Event %s is pending durable dispatch", event_id)
    return {"status": "accepted", "event_id": str(event_id)}
