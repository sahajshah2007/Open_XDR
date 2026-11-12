from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.schemas.incident import IncidentResponse, IncidentDetailResponse, IncidentUpdate, IncidentNoteCreate
from app.models.incident import Incident
import json
import redis
from datetime import datetime
from app.core.config import settings
from app.models.alert import Alert
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[IncidentResponse])
def get_incidents(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Incident)
    
    if status:
        query = query.filter(Incident.status == status)
    if severity:
        query = query.filter(Incident.severity == severity)
        
    incidents = query.order_by(Incident.last_seen.desc()).offset(skip).limit(limit).all()
    return incidents

@router.get("/{incident_id}", response_model=IncidentDetailResponse)
def get_incident(incident_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    return incident

def publish_incident_update(incident: Incident):
    try:
        redis_client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=0.5, socket_timeout=0.5)
        incident_dict = {
            "incident_id": str(incident.incident_id),
            "title": incident.title,
            "severity": incident.severity,
            "confidence": incident.confidence,
            "status": incident.status,
            "host_id": str(incident.host_id) if incident.host_id else None,
            "attack_story": incident.attack_story,
            "mitre_techniques": incident.mitre_techniques,
            "assignee_id": incident.assignee_id,
            "notes": incident.notes,
            "first_seen": incident.first_seen.isoformat() if incident.first_seen else None,
            "last_seen": incident.last_seen.isoformat() if incident.last_seen else None
        }
        payload = json.dumps({
            "type": "INCIDENT_UPDATE",
            "data": incident_dict
        })
        redis_client.publish("incidents_channel", payload)
        redis_client.close()
    except Exception as e:
        print(f"Redis publish failed: {e}")

@router.patch("/{incident_id}", response_model=IncidentResponse)
def update_incident(incident_id: uuid.UUID, update_data: IncidentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    if update_data.status is not None:
        incident.status = update_data.status
    # Check if we are intentionally unassigning (e.g. passing empty string)
    if "assignee_id" in update_data.model_fields_set:
        new_assignee = update_data.assignee_id if update_data.assignee_id else None
        if new_assignee:
            user = db.query(User).filter(User.id == new_assignee).first()
            if not user:
                raise HTTPException(status_code=400, detail="Invalid assignee_id")
        incident.assignee_id = new_assignee
        
    if "host_id" in update_data.model_fields_set:
        if update_data.host_id is not None:
            from app.models.host import Host
            if db.get(Host, update_data.host_id) is None:
                raise HTTPException(status_code=400, detail="Invalid host_id")
        incident.host_id = update_data.host_id
        
    db.commit()
    db.refresh(incident)
    publish_incident_update(incident)
    return incident

@router.post("/{incident_id}/notes", response_model=IncidentResponse)
def add_incident_note(incident_id: uuid.UUID, note_data: IncidentNoteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    notes = list(incident.notes) if incident.notes else []
    new_note = {
        "author": current_user.username,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "text": note_data.text
    }
    notes.append(new_note)
    incident.notes = notes
    
    db.commit()
    db.refresh(incident)
    publish_incident_update(incident)
    return incident
