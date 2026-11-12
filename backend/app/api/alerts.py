from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.schemas.alert import AlertResponse
from app.models.alert import Alert
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[AlertResponse])
def get_alerts(
    skip: int = 0,
    limit: int = 100,
    severity: Optional[str] = None,
    rule_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Alert)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    if rule_id:
        query = query.filter(Alert.rule_id == rule_id)
        
    alerts = query.order_by(Alert.timestamp.desc()).offset(skip).limit(limit).all()
    return alerts
