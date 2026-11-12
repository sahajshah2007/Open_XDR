from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class NormalizedEvent(BaseModel):
    event_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    timestamp: datetime
    source: str
    host_id: Optional[str] = None
    host_name: Optional[str] = None
    event_type: str
    severity: Optional[str] = None
    user: Optional[str] = None
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    process_name: Optional[str] = None
    process_id: Optional[int] = None
    command_line: Optional[str] = None
    file_path: Optional[str] = None
    message: Optional[str] = None
    mitre_tactic: Optional[str] = None
    mitre_technique: Optional[str] = None
    product: Optional[str] = None
    category: Optional[str] = None
    service: Optional[str] = None
    techniques: list[str] = Field(default_factory=list)
    raw: Dict[str, Any]

class RawIngestEvent(BaseModel):
    source: str
    data: Dict[str, Any]

    model_config = ConfigDict(extra="allow")

class EventResponse(NormalizedEvent):
    model_config = ConfigDict(from_attributes=True)
