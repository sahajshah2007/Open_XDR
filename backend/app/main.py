from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
from alembic import command
from alembic.config import Config
from app.core.config import settings

# Import all models to ensure SQLAlchemy metadata is registered properly
from app.core.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.host import Host
from app.models.event import Event
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.pipeline import PipelineJob, ResponseAction, IntegrationSetting
from app.models import experiment

from app.core.security import get_password_hash
from app.api import ingest, alerts, incidents, hosts, events, ws, settings as app_settings, auth, defense, experiments

@asynccontextmanager
async def lifespan(app: FastAPI):
    migration_config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(migration_config, "head")
    
    # Inject default admin user
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        if not admin:
            db.add(User(username=settings.ADMIN_USERNAME, hashed_password=get_password_hash(settings.ADMIN_PASSWORD)))
            db.commit()
    finally:
        db.close()
        
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Educational cyber defense simulation lab. Recorded and synthetic telemetry; simulated response actions only.",
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set up strict CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost", "http://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(ingest.router, prefix=f"{settings.API_V1_STR}/ingest", tags=["ingest"])
app.include_router(alerts.router, prefix=f"{settings.API_V1_STR}/alerts", tags=["alerts"])
app.include_router(incidents.router, prefix=f"{settings.API_V1_STR}/incidents", tags=["incidents"])
app.include_router(hosts.router, prefix=f"{settings.API_V1_STR}/hosts", tags=["hosts"])
app.include_router(events.router, prefix=f"{settings.API_V1_STR}/events", tags=["events"])
app.include_router(app_settings.router, prefix=f"{settings.API_V1_STR}/settings", tags=["settings"])
app.include_router(ws.router, prefix=f"{settings.API_V1_STR}", tags=["websockets"])
app.include_router(defense.router, prefix=f"{settings.API_V1_STR}", tags=["digital twin and defense"])

app.include_router(experiments.router,prefix=f"{settings.API_V1_STR}/experiments",tags=["simulation experiments"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
