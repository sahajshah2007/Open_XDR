"""Database-backed settings used consistently by API and Celery processes."""
import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings
from app.models.pipeline import IntegrationSetting


def cipher():
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(settings.JWT_SECRET.encode()).digest()))


def save_setting(db, name, value):
    row = db.get(IntegrationSetting, name)
    encrypted = cipher().encrypt(value.encode()).decode()
    if row is None:
        db.add(IntegrationSetting(name=name, encrypted_value=encrypted))
    else:
        row.encrypted_value = encrypted


def read_setting(db, name, default=""):
    row = db.get(IntegrationSetting, name)
    return cipher().decrypt(row.encrypted_value.encode()).decode() if row else default


_rule_version = None


def refresh_rules(db):
    global _rule_version
    version = read_setting(db, "rule_version", "initial")
    if version != _rule_version:
        from app.services.rules import rule_engine
        rule_engine.reload_rules()
        _rule_version = version
