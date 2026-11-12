from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.event import Event
from app.schemas.event import EventResponse
from app.api.auth import get_current_user

router = APIRouter()

@router.get("", response_model=List[EventResponse])
def search_events(
    q: Optional[str] = Query(None, description="Search query string"),
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Event)
    
    if q:
        search_term = f"%{q}%"
        # Search across basic fields and cast JSONB to string for full text search
        query = query.filter(
            or_(
                Event.source.ilike(search_term),
                Event.event_type.ilike(search_term),
                cast(Event.raw, String).ilike(search_term)
            )
        )
        
    events = query.order_by(Event.timestamp.desc()).offset(skip).limit(limit).all()
    
    response = []
    for event in events:
        # Reconstruct the NormalizedEvent structure
        resp_dict = {
            "event_id": event.event_id,
            "timestamp": event.timestamp,
            "source": event.source,
            "host_id": str(event.host_id) if event.host_id else None,
            "event_type": event.event_type,
            "raw": event.raw,
        }
        # Merge in the normalized fields (like src_ip, etc)
        resp_dict.update(event.normalized)
        
        # Ensure event_id is preserved from the DB row and not overwritten by normalized JSON if it's there
        resp_dict["event_id"] = event.event_id
        resp_dict["host_id"] = str(event.host_id) if event.host_id else None
        
        response.append(EventResponse(**resp_dict))
        
    return response
