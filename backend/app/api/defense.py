"""Authenticated digital-twin queries and auditable response simulations."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from acdt.policy_engine.engine import PolicyEngine
from acdt.response.executor import ResponseExecutor
from acdt.attack_engine.risk import risk_score, path_probability
from app.api.auth import get_current_user, require_admin
from app.core.config import settings
from app.core.database import get_db
from app.models.host import Host
from app.models.incident import Incident
from app.models.event import Event
from app.models.alert import Alert
from app.models.pipeline import PipelineJob, ResponseAction
from app.services import twin
from app.services.response_planning import propose_actions, simulate_proposal

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/defense/overview")
def overview(db: Session = Depends(get_db)):
    from datetime import timedelta
    start = datetime.now(timezone.utc).date() - timedelta(days=6)
    active = db.query(Incident).filter(Incident.status.in_(["open", "triage"]))
    rows = db.query(func.date(Incident.first_seen), func.count()).filter(Incident.first_seen >= start).group_by(func.date(Incident.first_seen)).all()
    critical_rows = db.query(func.date(Incident.first_seen), func.count()).filter(Incident.first_seen >= start, Incident.severity.in_(["high", "critical"])).group_by(func.date(Incident.first_seen)).all()
    totals, critical = {str(date): count for date, count in rows}, {str(date): count for date, count in critical_rows}
    chart = [{"date": (start + timedelta(days=day)).isoformat(), "incidents": totals.get((start + timedelta(days=day)).isoformat(), 0), "critical": critical.get((start + timedelta(days=day)).isoformat(), 0)} for day in range(7)]
    return {"active_incidents": active.count(), "critical_incidents": active.filter(Incident.severity.in_(["high", "critical"])).count(),
            "hosts": db.query(Host).count(), "failed_events": db.query(PipelineJob).filter(PipelineJob.status == "failed").count(), "chart": chart,
            "total_events": db.query(Event).count(), "total_alerts": db.query(Alert).count(),
            "total_incidents": db.query(Incident).count(),
            "simulated_actions": db.query(ResponseAction).filter(ResponseAction.status == "simulated").count()}


class ActionResponse(BaseModel):
    action_id: uuid.UUID
    incident_id: uuid.UUID
    policy_id: str
    action: str
    autonomy: str
    status: str
    result: dict | None
    created_at: datetime
    executed_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class PlanRequest(BaseModel):
    user: str | None = Field(None, max_length=128, pattern=r"^[\w.@-]+$")


class RiskRequest(BaseModel):
    edge_probabilities: list[float] = Field(min_length=1, max_length=10)
    asset_value: float = Field(ge=0, le=1_000_000)


@router.get("/defense/status")
def defense_status(db: Session = Depends(get_db)):
    processing = dict(db.query(PipelineJob.status, func.count()).group_by(PipelineJob.status).all())
    projection = dict(db.query(PipelineJob.twin_status, func.count()).group_by(PipelineJob.twin_status).all())
    policies = PolicyEngine(settings.POLICY_FILE).policies
    return {"name": settings.PROJECT_NAME, "execution_mode": "simulation", "twin_enabled": settings.NEO4J_ENABLED,
            "processing": processing, "projection": projection,
            "policies": [{"id": p.id, "description": p.description, "autonomy": p.autonomy} for p in policies]}


@router.get("/twin")
def get_twin(db: Session = Depends(get_db)):
    if not settings.NEO4J_ENABLED:
        return {"enabled":True, **twin.local_snapshot(db)}
    try:
        return {"enabled": True, **twin.twin_snapshot()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Digital twin is unavailable; event detection continues independently") from exc


@router.get("/twin/paths")
def get_paths(from_host: str = Query(min_length=1, max_length=255), db: Session = Depends(get_db)):
    if not settings.NEO4J_ENABLED:
        return {"from":from_host,"paths":twin.local_paths(db,from_host),"description":"Observed reachability in the local simulation model."}
    try:
        return {"from": from_host, "paths": twin.paths_to_critical(from_host),
                "description": "Observed connectivity to critical assets; exploitability is not established."}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Digital twin path query failed") from exc


@router.post("/defense/risk")
def estimate_path_risk(request: RiskRequest):
    if any(not 0 <= probability <= 1 for probability in request.edge_probabilities):
        raise HTTPException(status_code=422, detail="Probabilities must be between zero and one")
    return {"probability": path_probability(request.edge_probabilities),
            "risk": risk_score(request.edge_probabilities, request.asset_value),
            "assumption": "User-supplied independent edge probabilities; scenario estimate only"}


@router.get("/defense/actions", response_model=list[ActionResponse])
def list_actions(db: Session = Depends(get_db), limit: int = Query(100, ge=1, le=500)):
    return db.query(ResponseAction).order_by(ResponseAction.created_at.desc()).limit(limit).all()


@router.post("/defense/incidents/{incident_id}/plan", response_model=list[ActionResponse])
def plan_response(incident_id: uuid.UUID, request: PlanRequest, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    incident = db.get(Incident, incident_id, with_for_update=True)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    propose_actions(db,incident,current_user.id,request.user or '')
    db.commit()
    return db.query(ResponseAction).filter_by(incident_id=incident_id).all()


@router.post("/defense/actions/{action_id}/simulate", response_model=ActionResponse)
def simulate_action(action_id: uuid.UUID, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    action = db.get(ResponseAction, action_id, with_for_update=True)
    if action is None:
        raise HTTPException(status_code=404, detail="Response action not found")
    simulate_proposal(action,current_user.username)
    db.commit()
    db.refresh(action)
    return action


@router.post("/defense/events/{event_id}/retry")
def retry_event(event_id: uuid.UUID, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    job = db.get(PipelineJob, event_id, with_for_update=True)
    if job is None:
        raise HTTPException(status_code=404, detail="Processing record not found")
    if job.status != "processed":
        job.status, job.attempts, job.error = "pending", 0, None
    if job.twin_status == "failed":
        job.twin_status, job.twin_attempts, job.twin_error = "pending", 0, None
    db.commit()
    return {"status": "queued-for-dispatch", "event_id": event_id}
