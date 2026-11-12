from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from typing import Literal
from datetime import datetime
import uuid

from app.schemas.alert import AlertResponse

class IncidentBase(BaseModel):
    title: str
    severity: str
    confidence: int
    status: str
    host_id: Optional[uuid.UUID] = None
    first_seen: datetime
    last_seen: datetime
    attack_story: List[str] = []
    mitre_techniques: List[str] = []
    assignee_id: Optional[str] = None
    notes: List[Dict[str, Any]] = []

class IncidentUpdate(BaseModel):
    status: Optional[Literal["open", "triage", "closed", "false-positive"]] = None
    assignee_id: Optional[str] = None
    host_id: Optional[uuid.UUID] = None

class IncidentNoteCreate(BaseModel):
    text: str

class IncidentResponse(IncidentBase):
    incident_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IncidentDetailResponse(IncidentResponse):
    alerts: List[AlertResponse] = []
    
    model_config = ConfigDict(from_attributes=True)
