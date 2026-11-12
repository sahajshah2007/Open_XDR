import pytest
from sqlalchemy import create_engine
from app.core.config import Settings


@pytest.mark.parametrize("url, expected", [
    ("postgresql://user:password@localhost/db", "postgresql+psycopg2://user:password@localhost/db"),
    ("postgres://user:password@localhost/db", "postgresql+psycopg2://user:password@localhost/db"),
    ("postgresql+psycopg2://user:password@localhost/db", "postgresql+psycopg2://user:password@localhost/db"),
    ("postgresql+psycopg://user:password@localhost/db", "postgresql+psycopg://user:password@localhost/db"),
    ("sqlite://", "sqlite://"),
    ("postgresql://user:pass%40word@localhost/db?application_name=openxdr", "postgresql+psycopg2://user:pass%40word@localhost/db?application_name=openxdr"),
])
def test_database_urls_select_installed_driver_without_changing_connection_details(url, expected):
    configured = Settings(_env_file=None, DATABASE_URL=url)
    assert configured.DATABASE_URL == expected


def test_postgres_engine_loads_the_driver_installed_in_the_image():
    configured = Settings(_env_file=None, DATABASE_URL="postgresql://user:password@localhost/db")
    # Engine construction loads the DBAPI without contacting a live database.
    # SQLite-only startup tests did not exercise this production import path.
    engine = create_engine(configured.DATABASE_URL)
    try:
        assert engine.dialect.driver == "psycopg2"
        assert engine.dialect.dbapi.__name__ == "psycopg2"
    finally:
        engine.dispose()
