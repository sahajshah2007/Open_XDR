import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.update(DATABASE_URL="sqlite://", DEBUG="false", JWT_SECRET="test-secret-with-no-production-use", ADMIN_USERNAME="admin", ADMIN_PASSWORD="test-password", INGEST_API_KEY="test-ingest-key", NEO4J_ENABLED="false")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.services import detection
from app.services import experiments

settings.OTX_API_KEY = ""


@pytest.fixture
def db_setup(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(detection, "SessionLocal", sessions)
    monkeypatch.setattr(experiments, "SessionLocal", sessions)
    monkeypatch.setattr(experiments.finalize_experiment,"apply_async",lambda **kwargs: None)
    monkeypatch.setattr(detection.evaluate_and_alert, "apply_async", lambda **kwargs: None)
    monkeypatch.setattr(detection.project_event, "apply_async", lambda **kwargs: None)
    import app.api.incidents as incidents
    monkeypatch.setattr(incidents, "publish_incident_update", lambda incident: None)
    def override_db():
        with sessions() as db:
            yield db
    app.dependency_overrides[get_db] = override_db
    with sessions.begin() as db:
        db.add(User(id="admin-id", username="admin", hashed_password=get_password_hash("test-password"), is_active=True))
        db.add(User(id="analyst-id", username="analyst", hashed_password=get_password_hash("test-password"), is_active=True))
    yield sessions
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def client(db_setup):
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {create_access_token({'sub':'admin'})}"}
