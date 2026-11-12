"""Durable, idempotent processing for both projects' telemetry."""
import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from app.celery_app import celery_app
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.event import Event
from app.models.alert import Alert
from app.models.pipeline import PipelineJob
from app.models.experiment import EventAlert, ExperimentEvent, ExperimentRun
from app.schemas.event import NormalizedEvent
from app.services.rules import rule_engine, RuleEngine
from app.services.native_alerts import detections_for
from app.services.parsers.common import tactic_name

logger = logging.getLogger(__name__)


@celery_app.task(name="detection.evaluate_and_alert", acks_late=True)
def evaluate_and_alert(event_id: str):
    event_id = uuid.UUID(event_id)
    incident_ids = set()
    try:
        with SessionLocal.begin() as db:
            job = db.execute(select(PipelineJob).where(PipelineJob.event_id == event_id).with_for_update()).scalar_one()
            if job.status == "processed" or job.attempts >= settings.PIPELINE_MAX_ATTEMPTS:
                return
            stored = db.get(Event, event_id)
            event = NormalizedEvent(**stored.normalized)
            link = db.get(ExperimentEvent, event_id)
            run = db.get(ExperimentRun, link.run_id) if link else None
            config = run.snapshot.get('detection_config') if run else None
            if config:
                if config['engine_version'] != 1:
                    raise ValueError('Unsupported pinned detection engine version')
                rules = detections_for(event, enabled_sources=config['native_sources'], wazuh_min_level=config['wazuh_min_level'])
                rules += RuleEngine(rules=config['sigma_rules']).match_event(event.model_dump())
            else:
                # Imported evidence and pre-snapshot runs keep their original path.
                from app.services.configuration import refresh_rules
                refresh_rules(db)
                rules = detections_for(event) + rule_engine.match_event(event.model_dump())
            for rule in {rule["id"]: rule for rule in rules}.values():
                tactic, technique = event.mitre_tactic, event.mitre_technique
                for tag in rule.get("tags", []):
                    if tag.startswith("attack.t") and tag[8:9].isdigit():
                        technique = technique or tag[len("attack."):].upper()
                    elif tag.startswith("attack."):
                        tactic = tactic or tactic_name(tag[len("attack."):])
                alert = Alert(host_id=stored.host_id, rule_id=rule["id"], rule_name=rule["title"],
                              source=event.source, severity=rule.get("level", "medium"), confidence="rule-match",
                              mitre_tactic=tactic, mitre_technique=technique,
                              source_ip=event.src_ip, destination_ip=event.dst_ip,
                              timestamp=event.timestamp, raw_event=event.raw)
                db.add(alert)
                from app.services.enrichment import enrich_alert
                if event.raw.get("_lab"):
                    alert.enrichment = {"simulation": {"external_lookup": False}}
                else:
                    enrich_alert(alert, db)
                db.flush()
                db.add(EventAlert(event_id=event_id,alert_id=alert.alert_id))
                from app.services.correlate import correlate_alert
                incident = correlate_alert(db, alert)
                incident.mitre_techniques = sorted(set(incident.mitre_techniques or []) | set(event.techniques))
                incident_ids.add(incident.incident_id)
            job.status = "processed"
            job.attempts += 1
            job.error = None
            job.processed_at = datetime.now(timezone.utc)
    except Exception as exc:
        with SessionLocal.begin() as db:
            job = db.get(PipelineJob, event_id, with_for_update=True)
            if job and job.status != "processed":
                job.status = "failed"
                job.attempts += 1
                job.error = str(exc)[:2000]
        logger.exception("Event %s failed processing", event_id)
        raise
    # Notify only after the incident transaction committed.
    from app.api.incidents import publish_incident_update
    from app.models.incident import Incident
    with SessionLocal() as db:
        for incident_id in incident_ids:
            publish_incident_update(db.get(Incident, incident_id))
    run_id = event.raw.get("_lab",{}).get("run_id")
    if run_id:
        from app.services.experiments import finalize_experiment
        try:
            finalize_experiment.apply_async(args=[run_id],retry=False)
        except Exception:
            logger.warning("Experiment %s awaits scheduled finalization",run_id)
    if settings.NEO4J_ENABLED:
        try:
            project_event.apply_async(args=[str(event_id)], retry=False)
        except Exception:
            logger.warning("Twin projection pending for %s", event_id)


@celery_app.task(name="detection.dispatch_pending")
def dispatch_pending():
    with SessionLocal() as db:
        jobs = db.query(PipelineJob).filter(PipelineJob.status != "processed", PipelineJob.attempts < settings.PIPELINE_MAX_ATTEMPTS).limit(100).all()
        for job in jobs:
            evaluate_and_alert.apply_async(args=[str(job.event_id)], retry=False)
        if settings.NEO4J_ENABLED:
            for job in db.query(PipelineJob).filter(PipelineJob.status == "processed", PipelineJob.twin_status.in_(["pending", "failed"]), PipelineJob.twin_attempts < settings.PIPELINE_MAX_ATTEMPTS).limit(100):
                project_event.apply_async(args=[str(job.event_id)], retry=False)


@celery_app.task(name="detection.project_event", acks_late=True)
def project_event(event_id: str):
    if not settings.NEO4J_ENABLED:
        return
    event_id = uuid.UUID(event_id)
    from app.services.twin import project_to_twin
    try:
        with SessionLocal.begin() as db:
            job = db.get(PipelineJob, event_id, with_for_update=True)
            if job.twin_status == "synced":
                return
            project_to_twin(db, db.get(Event, event_id))
            job.twin_status = "synced"
            job.twin_error = None
            job.twin_attempts += 1
    except Exception as exc:
        with SessionLocal.begin() as db:
            job = db.get(PipelineJob, event_id, with_for_update=True)
            if job.twin_status != "synced":
                job.twin_status = "failed"
                job.twin_error = str(exc)[:2000]
                job.twin_attempts += 1
        raise
