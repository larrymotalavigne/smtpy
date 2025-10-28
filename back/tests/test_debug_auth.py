"""Debug test to see actual auth errors."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from api.main import create_app
from shared.core.config import SETTINGS
from shared.models.base import Base


@pytest_asyncio.fixture
async def debug_client():
    """Create a simple async client for debugging."""
    # Use in-memory SQLite for quick testing
    async_url = "sqlite+aiosqlite:///:memory:"

    # Patch settings
    original_url = SETTINGS.DATABASE_URL
    SETTINGS.DATABASE_URL = async_url

    # Create engine and tables
    import api.core.db as db_module
    original_engine = db_module.async_engine
    original_sessionmaker = db_module.async_sessionmaker_factory

    test_engine = create_async_engine(async_url, echo=True)
    test_sessionmaker = async_sessionmaker(test_engine, expire_on_commit=False)

    db_module.async_engine = test_engine
    db_module.async_sessionmaker_factory = test_sessionmaker

    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create app
    app = create_app()

    # Create client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Cleanup
    await test_engine.dispose()
    db_module.async_engine = original_engine
    db_module.async_sessionmaker_factory = original_sessionmaker
    SETTINGS.DATABASE_URL = original_url


@pytest.mark.asyncio
async def test_debug_login(debug_client):
    """Debug login to see actual error."""
    # Register
    reg_response = await debug_client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123!"
    })
    print(f"\nRegister response: {reg_response.status_code}")
    print(f"Register data: {reg_response.json()}")

    # Login
    login_response = await debug_client.post("/auth/login", json={
        "username": "testuser",
        "password": "SecurePass123!"
    })
    print(f"\nLogin response: {login_response.status_code}")
    print(f"Login data: {login_response.text}")

    if login_response.status_code != 200:
        print(f"Login failed with status {login_response.status_code}")
        print(f"Response: {login_response.text}")
