"""
Global test fixtures for SMTPy backend tests.

This file provides fixtures for database setup, HTTP clients, and test utilities.
Uses PostgreSQL testcontainers for realistic integration testing.

Reference: http://alexmic.net/flask-sqlalchemy-pytest/
"""
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

# Ensure the project root is in the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Define ROOT_DIR as the back/ directory
ROOT_DIR = Path(__file__).parent.parent

# Set test environment variables
os.environ["TESTING"] = "True"


# ============================================================================
# Session-scoped Event Loop
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for all async tests.

    This prevents "Future attached to a different loop" and
    "Event loop is closed" errors by ensuring all session-scoped
    async fixtures bind to the same loop as the tests.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# ============================================================================
# Settings Configuration
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def patch_settings():
    """Patch SETTINGS for test environment."""
    from shared.core.config import SETTINGS

    # Store original values
    original_database_url = SETTINGS.DATABASE_URL
    original_debug = SETTINGS.DEBUG
    original_secret = SETTINGS.SECRET_KEY
    original_stripe_key = SETTINGS.STRIPE_API_KEY
    original_stripe_secret = SETTINGS.STRIPE_WEBHOOK_SECRET

    # Set test values
    SETTINGS.DEBUG = True
    SETTINGS.SECRET_KEY = "test-secret-key-for-testing-only"
    SETTINGS.STRIPE_API_KEY = "sk_test_fake_key_for_testing"
    SETTINGS.STRIPE_WEBHOOK_SECRET = "whsec_fake_secret_for_testing"

    yield SETTINGS

    # Restore original values
    SETTINGS.DATABASE_URL = original_database_url
    SETTINGS.DEBUG = original_debug
    SETTINGS.SECRET_KEY = original_secret
    SETTINGS.STRIPE_API_KEY = original_stripe_key
    SETTINGS.STRIPE_WEBHOOK_SECRET = original_stripe_secret


# ============================================================================
# PostgreSQL Testcontainer Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def postgres_container(event_loop):
    """Start PostgreSQL testcontainer for the entire test session."""
    container = PostgresContainer(
        image="postgres:18",
        driver="psycopg"  # Use psycopg (v3) driver
    )
    container.start()

    yield container

    container.stop()


@pytest_asyncio.fixture(scope="session")
async def async_engine(postgres_container, patch_settings, event_loop):
    """Create async SQLAlchemy engine connected to PostgreSQL testcontainer."""
    from shared.models.base import Base

    # Get connection URL from container
    db_url = postgres_container.get_connection_url()

    # Convert to async URL (psycopg3 async driver)
    async_url = db_url.replace("postgresql+psycopg://", "postgresql+psycopg://")
    if not async_url.startswith("postgresql+psycopg://"):
        async_url = db_url.replace("postgresql://", "postgresql+psycopg://")

    # Update settings with test database URL
    patch_settings.DATABASE_URL = async_url

    # Create async engine
    engine = create_async_engine(
        async_url,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=5,
        max_overflow=10
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup: drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# ============================================================================
# Database Session Fixtures
# ============================================================================

@pytest_asyncio.fixture(scope="class", autouse=True)
async def clean_database(async_engine):
    """Clean all database tables at the class level.

    This runs once per test class to avoid excessive cleanup overhead.
    Uses PostgreSQL-specific session_replication_role for faster truncation.
    """
    from shared.models.base import Base

    async with async_engine.begin() as conn:
        # Disable foreign key checks temporarily for faster cleanup
        await conn.execute(text("SET session_replication_role = 'replica';"))

        # Truncate all tables
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))

        # Re-enable foreign key checks
        await conn.execute(text("SET session_replication_role = 'origin';"))


@pytest_asyncio.fixture(scope="function")
async def async_db(async_engine):
    """Provide async database session for each test function.

    This fixture:
    - Creates a new session for each test
    - Cleans all tables before the test
    - Automatically rolls back after the test
    """
    from shared.models.base import Base

    # Create session maker
    testing_async_session_local = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        bind=async_engine
    )

    async with testing_async_session_local() as session:
        # Clear all tables before each test
        try:
            # Use TRUNCATE for better performance on PostgreSQL
            await session.execute(text("SET session_replication_role = 'replica';"))
            for table in reversed(Base.metadata.sorted_tables):
                await session.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))
            await session.execute(text("SET session_replication_role = 'origin';"))
            await session.commit()
        except Exception as e:
            await session.rollback()
            # If TRUNCATE fails, fall back to DELETE
            for table in reversed(Base.metadata.sorted_tables):
                await session.execute(text(f"DELETE FROM {table.name}"))
            await session.commit()

        yield session

        # Rollback any uncommitted changes
        try:
            await session.rollback()
        except Exception:
            pass


# ============================================================================
# HTTP Client Fixtures
# ============================================================================

@pytest_asyncio.fixture(scope="session")
async def client(async_engine, patch_settings, event_loop):
    """Create async HTTP client with test database for the entire session.

    This fixture:
    - Creates a FastAPI test client
    - Overrides the database dependency to use test database
    - Shares the same PostgreSQL container across all tests
    """
    from api.main import create_app
    from shared.core.db import get_async_session

    # Create test session maker
    testing_async_session_local = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        bind=async_engine
    )

    # Dependency override for database sessions
    async def get_test_db():
        async with testing_async_session_local() as session:
            yield session

    # Create FastAPI app
    app = create_app()

    # Override database dependency
    app.dependency_overrides[get_async_session] = get_test_db

    # Create async HTTP client
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c

    # Clear overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def authenticated_client(client, async_db):
    """Create an authenticated HTTP client for testing protected endpoints.

    This fixture:
    - Registers a test user
    - Logs in to get session cookies
    - Returns client with valid authentication

    Usage:
        async def test_protected_endpoint(authenticated_client):
            response = await authenticated_client.get("/api/protected")
            assert response.status_code == 200
    """
    # Register test user
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123!"
    }

    register_response = await client.post("/auth/register", json=register_data)

    # If registration fails, user might already exist - try to login anyway
    if register_response.status_code not in [200, 201]:
        pass  # Continue to login

    # Login to get session cookies
    login_data = {
        "username": "testuser",
        "password": "SecurePass123!"
    }

    login_response = await client.post("/auth/login", json=login_data)

    if login_response.status_code != 200:
        # If login fails, re-raise for debugging
        raise Exception(f"Authentication failed: {login_response.status_code} - {login_response.text}")

    # Client now has session cookies
    yield client


# ============================================================================
# Synchronous Database Fixtures (for legacy tests)
# ============================================================================

@pytest.fixture(scope="session")
def sync_engine(postgres_container):
    """Create synchronous SQLAlchemy engine for legacy tests."""
    from shared.models.base import Base

    # Get connection URL from container
    db_url = postgres_container.get_connection_url()

    # Create sync engine
    engine = create_engine(db_url, echo=False)

    # Create all tables
    Base.metadata.create_all(engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="class")
def db(sync_engine):
    """Provide synchronous database session for legacy tests."""
    from shared.models.base import Base

    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        bind=sync_engine
    )

    db = testing_session_local()

    # Clear all tables
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(text(f"DELETE FROM {table.name}"))
    db.commit()

    yield db

    db.close()


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def mock_smtp(monkeypatch):
    """Mock SMTP client to prevent actual email sending during tests."""
    with patch("smtplib.SMTP"):
        yield


@pytest.fixture(autouse=True)
def mock_stripe(monkeypatch):
    """Mock Stripe API calls to prevent actual API requests during tests."""
    # This can be expanded to mock specific Stripe methods
    # For now, we rely on test API keys
    yield


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def test_organization(async_db):
    """Create a test organization for tests that need one."""
    from shared.models.organization import Organization

    org = Organization(
        id=1,
        name="Test Organization",
        email="org@test.com",
        stripe_customer_id="cus_test_123",
        subscription_status=None
    )
    async_db.add(org)
    await async_db.commit()
    await async_db.refresh(org)

    return org


@pytest_asyncio.fixture
async def test_domain(async_db, test_organization):
    """Create a test domain for tests that need one.

    Depends on test_organization fixture.
    """
    from shared.models.domain import Domain, DomainStatus

    domain = Domain(
        id=1,
        name="test.example.com",
        organization_id=test_organization.id,
        status=DomainStatus.VERIFIED,
        is_active=True,
        mx_record_verified=True,
        spf_record_verified=True,
        dkim_record_verified=True,
        dmarc_record_verified=True
    )
    async_db.add(domain)
    await async_db.commit()
    await async_db.refresh(domain)

    return domain


@pytest_asyncio.fixture
async def test_user(async_db, test_organization):
    """Create a test user for tests that need one.

    Depends on test_organization fixture.
    """
    from shared.models.user import User, UserRole
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    user = User(
        id=1,
        username="testuser",
        email="testuser@test.com",
        password_hash=pwd_context.hash("TestPassword123!"),
        role=UserRole.ADMIN,
        organization_id=test_organization.id,
        is_active=True,
        email_verified=True
    )
    async_db.add(user)
    await async_db.commit()
    await async_db.refresh(user)

    return user
