from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.main as main
from app.core.config import settings
from app.core.database import get_db


def test_actual_startup_migrates_and_seeds_admin(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'startup.db'}"
    monkeypatch.setattr(settings, 'DATABASE_URL', url)
    engine = create_engine(url, connect_args={'check_same_thread':False})
    sessions = sessionmaker(bind=engine)
    monkeypatch.setattr(main, 'SessionLocal', sessions)
    def get_session():
        with sessions() as db:
            yield db
    main.app.dependency_overrides[get_db] = get_session
    try:
        with TestClient(main.app) as client:
            assert client.get('/health').status_code == 200
            login = client.post('/api/v1/auth/login', data={'username':'admin','password':'test-password'})
            assert login.status_code == 200, login.text
            headers = {'Authorization':f"Bearer {login.json()['access_token']}"}
            assert client.get('/api/v1/defense/status', headers=headers).status_code == 200
    finally:
        main.app.dependency_overrides.clear()
        engine.dispose()
