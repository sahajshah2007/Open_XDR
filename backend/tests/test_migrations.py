from pathlib import Path
import logging
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from app.core.config import settings
from app.core.database import Base


@pytest.mark.parametrize("database_state", ["fresh", "unversioned", "legacy_revision"])
def test_migration_creates_new_database_and_preserves_legacy_tables(tmp_path, monkeypatch, database_state):
    url = f"sqlite:///{tmp_path / 'migration.db'}"
    engine = create_engine(url)
    if database_state != "fresh":
        for table in Base.metadata.sorted_tables:
            if table.name in {'users','hosts','events','alerts','incidents'}:
                table.create(engine)
        with engine.begin() as conn:
            conn.exec_driver_sql("INSERT INTO users (id,username,hashed_password,is_active) VALUES ('original','original-user','original-hash',1)")
            if database_state == "legacy_revision":
                conn.exec_driver_sql("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)")
                conn.exec_driver_sql("INSERT INTO alembic_version VALUES ('95faffc550e2')")
    monkeypatch.setattr(settings, 'DATABASE_URL', url)
    config = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
    startup_logger = logging.getLogger("uvicorn.error")
    startup_logger.disabled = False
    command.upgrade(config, 'head')
    command.upgrade(config, 'head')
    assert not startup_logger.disabled
    assert set(Base.metadata.tables).issubset(inspect(engine).get_table_names())
    with engine.connect() as conn:
        assert conn.exec_driver_sql("SELECT version_num FROM alembic_version").scalar() == "0003_detection_profiles"
        if database_state != "fresh":
            assert conn.exec_driver_sql("SELECT username FROM users WHERE id='original'").scalar() == 'original-user'
    engine.dispose()
