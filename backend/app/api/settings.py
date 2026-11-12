import uuid
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.api.auth import require_admin
from app.core.database import get_db
from app.services.configuration import save_setting
from app.services.rules import rule_engine

router = APIRouter()


class SettingsUpdate(BaseModel):
    otx_api_key: str = Field(max_length=512, pattern=r"^[^\r\n]*$")


@router.post("/otx-key")
def update_otx_key(settings: SettingsUpdate, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    save_setting(db, "otx_api_key", settings.otx_api_key)
    db.commit()
    return {"status": "success", "message": "OTX key saved for API and workers"}


@router.post("/reload-rules")
def reload_rules(db: Session = Depends(get_db), current_user=Depends(require_admin)):
    count = rule_engine.reload_rules()
    save_setting(db, "rule_version", str(uuid.uuid4()))
    db.commit()
    return {"status": "success", "message": f"Loaded {count} rules; workers refresh before their next event"}
