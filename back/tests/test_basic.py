from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from api.main import create_app
from api.core.db import get_db

# Create test database
test_database_url = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(test_database_url, echo=False)
test_sessionmaker = async_sessionmaker(
    bind=test_engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

async def get_test_db():
    """Override get_db for testing."""
    async with test_sessionmaker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Create database tables
async def create_test_tables():
    from api.models.base import Base
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Setup for testing
import asyncio
asyncio.run(create_test_tables())

# Create app and override dependency
app = create_app()
app.dependency_overrides[get_db] = get_test_db
client = TestClient(app)


def test_health_check_root():
    """Test that the root health check endpoint works"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "SMTPy v2 API"


def test_health_check_detailed():
    """Test that the detailed health check endpoint works"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "SMTPy v2 API"
    assert data["version"] == "2.0.0"
    assert "domains" in data["features"]
    assert "messages" in data["features"]
    assert "billing" in data["features"]


def test_domains_endpoint_exists():
    """Test that domains endpoint exists (even if it returns empty data)"""
    response = client.get("/domains")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data


def test_messages_endpoint_exists():
    """Test that messages endpoint exists (even if it returns empty data)"""
    response = client.get("/messages")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
