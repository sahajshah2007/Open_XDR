from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.core.database import get_db
from app.models.host import Host
from app.schemas.host import HostResponse, HostUpdate
from app.api.auth import get_current_user

router = APIRouter()

@router.get("", response_model=List[HostResponse])
def get_hosts(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    hosts = db.query(Host).order_by(Host.last_seen.desc()).all()
    return hosts

@router.get("/{host_id}", response_model=HostResponse)
def get_host(host_id: uuid.UUID, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    host = db.query(Host).filter(Host.host_id == host_id).first()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    return host

@router.patch("/{host_id}", response_model=HostResponse)
def update_host(host_id: uuid.UUID, update_data: HostUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    host = db.query(Host).filter(Host.host_id == host_id).first()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
        
    if update_data.criticality is not None:
        host.criticality = update_data.criticality
        
    if update_data.tags is not None:
        host.tags = update_data.tags
        
    db.commit()
    db.refresh(host)
    return host
