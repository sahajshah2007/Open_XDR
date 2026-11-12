from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Union
import uuid
from datetime import datetime

class HostBase(BaseModel):
    host_name: str
    os_name: Optional[str] = None
    os_version: Optional[str] = None
    agent_type: Optional[str] = None
    tags: Optional[Union[Dict[str, Any], List[str]]] = None
    criticality: Optional[int] = 1

class HostUpdate(BaseModel):
    tags: Optional[Union[Dict[str, Any], List[str]]] = None
    criticality: Optional[int] = Field(None, ge=1, le=10)

class HostResponse(HostBase):
    host_id: uuid.UUID
    first_seen: datetime
    last_seen: datetime

    model_config = ConfigDict(from_attributes=True)
