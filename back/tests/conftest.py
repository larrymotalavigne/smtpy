import sys
from pathlib import Path
from unittest.mock import patch

# Ensure the project root is in the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import pytest_asyncio

try:
    from alembic.command import upgrade
    from alembic.config import Config

    ALEMBIC_AVAILABLE = True
except ImportError:
    upgrade = None
    Config = None
    ALEMBIC_AVAILABLE = False
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from core.database.models import Base

# Define ROOT_DIR as the back/ directory
ROOT_DIR = Path(__file__).parent.parent


@pytest.fixture(scope="session", autouse=True)
def patch_settings():
    """Patch SETTINGS to use test database configuration."""
    container = PostgresContainer(image="postgres:17", driver="psycopg")
    container.start()
    url = container.get_connection_url()
    # Convert to async URL for proper async database connection
    async_url = url.replace("postgresql://", "postgresql+asyncpg://")

    with patch("core.config.SETTINGS") as mock_settings, \
         patch("core.utils.db.SYNC_DATABASE_URI", url), \
         patch("core.utils.db.SYNC_ENGINE") as mock_sync_engine, \
         patch("core.utils.db.SYNC_LOCAL_SESSION") as mock_sync_session:
        
        # Patch settings
        mock_settings.DATABASE_URL = url
        mock_settings.ASYNC_SQLALCHEMY_DATABASE_URI = async_url
        
        # Create sync engine and session for tests
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        sync_engine = create_engine(url, pool_pre_ping=True, pool_recycle=3600)
        sync_session_maker = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=sync_engine)
        mock_sync_engine.configure_mock(return_value=sync_engine)
        mock_sync_session.configure_mock(side_effect=lambda: sync_session_maker())
        
        yield url

    container.stop()


@pytest.fixture(scope="session")
def engine(patch_settings):
    url = patch_settings
    engine = create_engine(url)

    if ALEMBIC_AVAILABLE:
        # Use alembic to create database schema
        config = Config(f"{ROOT_DIR}/alembic.ini")
        config.set_main_option("sqlalchemy.url", url)
        config.set_main_option("script_location", f"{ROOT_DIR}/alembic")
        upgrade(config, "head")
    else:
        # Fallback: create tables directly from models
        from core.database.models import Base
        Base.metadata.create_all(engine)

    yield engine


@pytest.fixture(scope="class")
def db(engine):
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)
    db = testing_session_local()
    db.execute(text("SET session_replication_role = 'replica';"))
    for mapper in Base.registry.mappers:
        db.execute(text(f"TRUNCATE TABLE {mapper.tables[0].name} CASCADE"))
    db.execute(text("SET session_replication_role = 'origin';"))
    yield db
    db.close()


@pytest.fixture(scope="session")
def async_engine(patch_settings):
    """Create async engine for testing that matches the app's async database setup."""
    url = patch_settings
    async_url = url.replace("postgresql://", "postgresql+asyncpg://")
    from sqlalchemy.ext.asyncio import create_async_engine
    engine = create_async_engine(
        async_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=5,
        echo=False
    )
    yield engine
    engine.sync_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_db(async_engine):
    """Provide async database session for tests that need async database access."""
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from sqlalchemy import text as sync_text

    testing_async_session_local = async_sessionmaker(
        autocommit=False, autoflush=False, expire_on_commit=False, bind=async_engine
    )

    async with testing_async_session_local() as session:
        # Clear all tables before each test
        try:
            await session.execute(sync_text("SET session_replication_role = 'replica';"))
            for mapper in Base.registry.mappers:
                await session.execute(sync_text(f"TRUNCATE TABLE {mapper.tables[0].name} CASCADE"))
            await session.execute(sync_text("SET session_replication_role = 'origin';"))
            await session.commit()
        except Exception:
            await session.rollback()

        yield session

        try:
            await session.rollback()
        except Exception:
            pass


@pytest_asyncio.fixture(autouse=True)
def mock(monkeypatch):
    with (
        patch("core.utils.user.send_verification_email"),
        patch("core.utils.user.send_invitation_email"),
        patch("smtplib.SMTP"),
        patch("core.utils.csrf.validate_csrf") as mock_csrf,
    ):
        mock_csrf.return_value = None
        yield
