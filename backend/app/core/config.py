import os
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "TwinTrace Lab"
    PROJECT_VERSION: str = "0.4.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql+psycopg2://openxdr:change_me@localhost:5432/openxdr"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security & Auth
    JWT_SECRET: str
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str
    
    # Ingest
    INGEST_API_KEY: str

    RULES_DIR: str = str(Path(__file__).resolve().parents[3] / "rules" / "local")
    POLICY_FILE: str = str(Path(__file__).resolve().parents[2] / "config" / "policies.yaml")
    NEO4J_ENABLED: bool = False
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = ""
    OTX_API_KEY: str = ""
    PIPELINE_MAX_ATTEMPTS: int = 5
    TELEMETRY_STREAM: str = "telemetry_stream"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def select_postgres_driver(cls, value):
        # The image ships psycopg2. Keep older .env files working even when
        # SQLAlchemy changes the default driver for a bare PostgreSQL URL.
        if isinstance(value, str):
            for prefix in ("postgresql://", "postgres://"):
                if value.startswith(prefix):
                    return "postgresql+psycopg2://" + value[len(prefix):]
        return value

    model_config = SettingsConfigDict(
        env_file=(Path(__file__).resolve().parents[3] / ".env",
                  Path(__file__).resolve().parents[2] / ".env"),
        env_ignore_empty=True,
        extra="ignore",
    )

settings = Settings()
