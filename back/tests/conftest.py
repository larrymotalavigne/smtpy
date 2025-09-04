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


# Define ROOT_DIR as the back/ directory
ROOT_DIR = Path(__file__).parent.parent


@pytest.fixture(scope="session", autouse=True)
def patch_settings():
    """Patch SETTINGS to use test database configuration."""
    # Use SQLite in-memory database for testing
    async_url = "sqlite+aiosqlite:///:memory:"

    # Import the settings module to patch it properly
    from api.core.config import SETTINGS
    
    # Create a patch that modifies the actual SETTINGS instance
    original_database_url = SETTINGS.DATABASE_URL
    original_debug = SETTINGS.DEBUG
    original_secret = SETTINGS.SECRET_KEY
    original_stripe_key = SETTINGS.STRIPE_API_KEY
    original_stripe_secret = SETTINGS.STRIPE_WEBHOOK_SECRET

    # Set test values directly on the SETTINGS object
    SETTINGS.DATABASE_URL = async_url
    SETTINGS.DEBUG = True
    SETTINGS.SECRET_KEY = "test-secret-key"
    SETTINGS.STRIPE_API_KEY = "sk_test_fake_key"
    SETTINGS.STRIPE_WEBHOOK_SECRET = "whsec_fake_secret"
    
    try:
        yield async_url
    finally:
        # Restore original values
        SETTINGS.DATABASE_URL = original_database_url
        SETTINGS.DEBUG = original_debug
        SETTINGS.SECRET_KEY = original_secret
        SETTINGS.STRIPE_API_KEY = original_stripe_key
        SETTINGS.STRIPE_WEBHOOK_SECRET = original_stripe_secret


@pytest.fixture(scope="session")
def engine(patch_settings):
    url = patch_settings
    engine = create_engine(url)

    # Create tables directly from models (skip alembic for SQLite testing)
    from api.models.base import Base
    Base.metadata.create_all(engine)

    yield engine


@pytest.fixture(scope="class")
def db(engine):
    from api.models.base import Base
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)
    db = testing_session_local()
    # Clear all tables (SQLite compatible)
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(text(f"DELETE FROM {table.name}"))
    db.commit()
    yield db
    db.close()


@pytest.fixture(scope="session")
def async_engine(patch_settings):
    """Create async engine for testing that matches the app's async database setup."""
    url = patch_settings
    from sqlalchemy.ext.asyncio import create_async_engine
    
    # SQLite doesn't support pool_size, pool_recycle parameters
    if url.startswith("sqlite"):
        engine = create_async_engine(url, echo=False)
    else:
        # PostgreSQL configuration
        async_url = url.replace("postgresql://", "postgresql+asyncpg://")
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

    # Create tables first
    from api.models.base import Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    testing_async_session_local = async_sessionmaker(
        autocommit=False, autoflush=False, expire_on_commit=False, bind=async_engine
    )

    async with testing_async_session_local() as session:
        # Clear all tables before each test (SQLite compatible)
        try:
            for table in reversed(Base.metadata.sorted_tables):
                await session.execute(sync_text(f"DELETE FROM {table.name}"))
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
    # Mock SMTP for email sending (if needed)
    with patch("smtplib.SMTP"):
        yield
