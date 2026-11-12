from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

class AlertResponse(BaseModel):
    alert_id: uuid.UUID
    incident_id: Optional[uuid.UUID] = None
    host_id: Optional[uuid.UUID] = None
    rule_id: str
    rule_name: str
    severity: str
    confidence: Optional[str] = None
    mitre_tactic: Optional[str] = None
    mitre_technique: Optional[str] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    timestamp: datetime
    enrichment: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)
