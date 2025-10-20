"""Integration tests for authentication with real PostgreSQL database using testcontainers."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
import asyncio
import httpx

from api.main import create_app
from api.models import Base, User, UserRole
from api.database.users_database import UsersDatabase
from api.core.config import SETTINGS


# Testcontainer fixture for PostgreSQL
@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for testing."""
    with PostgresContainer("postgres:16") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def async_engine(postgres_container):
    """Create async engine for PostgreSQL container."""
    # Get connection URL from container
    db_url = postgres_container.get_connection_url()

    # Convert to async URL
    async_url = db_url.replace("psycopg2", "psycopg").replace("postgresql://", "postgresql+psycopg://")

    # Patch settings to use container database
    original_url = SETTINGS.DATABASE_URL
    SETTINGS.DATABASE_URL = async_url

    engine = create_async_engine(async_url, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

    # Restore original settings
    SETTINGS.DATABASE_URL = original_url


@pytest_asyncio.fixture
async def async_session(async_engine):
    """Create async session for each test."""
    async_session_maker = async_sessionmaker(
        async_engine, expire_on_commit=False
    )

    async with async_session_maker() as session:
        # Clear all tables before test
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(text(f"DELETE FROM {table.name}"))
        await session.commit()

        yield session

        # Rollback any uncommitted changes
        await session.rollback()


@pytest_asyncio.fixture
async def client(postgres_container):
    """Create async HTTP client with test database."""
    import api.core.db as db_module

    # Get database URL
    db_url = postgres_container.get_connection_url()
    async_url = db_url.replace("psycopg2", "psycopg").replace("postgresql://", "postgresql+psycopg://")

    # Patch settings
    original_url = SETTINGS.DATABASE_URL
    SETTINGS.DATABASE_URL = async_url

    # Replace the engine and session maker with test versions
    original_engine = db_module.async_engine
    original_sessionmaker = db_module.async_sessionmaker_factory

    test_engine = create_async_engine(async_url, echo=False)
    test_sessionmaker = async_sessionmaker(test_engine, expire_on_commit=False)

    db_module.async_engine = test_engine
    db_module.async_sessionmaker_factory = test_sessionmaker

    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create app
    app = create_app()

    # Use httpx AsyncClient with ASGI transport for async testing
    # Enable cookie handling with follow_redirects and cookies
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
        follow_redirects=True
    ) as ac:
        yield ac

    # Cleanup
    await test_engine.dispose()

    # Restore original engine and settings
    db_module.async_engine = original_engine
    db_module.async_sessionmaker_factory = original_sessionmaker
    SETTINGS.DATABASE_URL = original_url


class TestUserRegistration:
    """Test user registration."""

    @pytest.mark.asyncio
    async def test_create_user(self, async_session):
        """Test creating a user in the database."""
        user = await UsersDatabase.create_user(
            session=async_session,
            username="testuser",
            email="test@example.com",
            password="SecurePass123!",
            role=UserRole.USER
        )

        await async_session.commit()

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_verified is False
        assert user.role == UserRole.USER
        assert user.verify_password("SecurePass123!") is True

    @pytest.mark.asyncio
    async def test_create_duplicate_username(self, async_session):
        """Test that duplicate usernames are prevented."""
        # Create first user
        await UsersDatabase.create_user(
            session=async_session,
            username="testuser",
            email="test1@example.com",
            password="SecurePass123!"
        )
        await async_session.commit()

        # Try to create second user with same username
        with pytest.raises(Exception):  # Should raise IntegrityError
            await UsersDatabase.create_user(
                session=async_session,
                username="testuser",
                email="test2@example.com",
                password="SecurePass123!"
            )
            await async_session.commit()

    @pytest.mark.asyncio
    async def test_create_duplicate_email(self, async_session):
        """Test that duplicate emails are prevented."""
        # Create first user
        await UsersDatabase.create_user(
            session=async_session,
            username="testuser1",
            email="test@example.com",
            password="SecurePass123!"
        )
        await async_session.commit()

        # Try to create second user with same email
        with pytest.raises(Exception):  # Should raise IntegrityError
            await UsersDatabase.create_user(
                session=async_session,
                username="testuser2",
                email="test@example.com",
                password="SecurePass123!"
            )
            await async_session.commit()


class TestUserAuthentication:
    """Test user authentication."""

    @pytest.mark.asyncio
    async def test_verify_password_correct(self, async_session):
        """Test password verification with correct credentials."""
        # Create user
        await UsersDatabase.create_user(
            session=async_session,
            username="testuser",
            email="test@example.com",
            password="SecurePass123!"
        )
        await async_session.commit()

        # Verify with username
        user = await UsersDatabase.verify_password(
            session=async_session,
            username_or_email="testuser",
            password="SecurePass123!"
        )

        assert user is not None
        assert user.username == "testuser"
        assert user.last_login is not None

    @pytest.mark.asyncio
    async def test_verify_password_with_email(self, async_session):
        """Test password verification using email."""
        # Create user
        await UsersDatabase.create_user(
            session=async_session,
            username="testuser",
            email="test@example.com",
            password="SecurePass123!"
        )
        await async_session.commit()

        # Verify with email
        user = await UsersDatabase.verify_password(
            session=async_session,
            username_or_email="test@example.com",
            password="SecurePass123!"
        )

        assert user is not None
        assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_verify_password_incorrect(self, async_session):
        """Test password verification with incorrect password."""
        # Create user
        await UsersDatabase.create_user(
            session=async_session,
            username="testuser",
            email="test@example.com",
            password="SecurePass123!"
        )
        await async_session.commit()

        # Try with wrong password
        user = await UsersDatabase.verify_password(
            session=async_session,
            username_or_email="testuser",
            password="WrongPassword!"
        )

        assert user is None

    @pytest.mark.asyncio
    async def test_verify_password_inactive_user(self, async_session):
        """Test that inactive users cannot login."""
        # Create user
        user = await UsersDatabase.create_user(
            session=async_session,
            username="testuser",
            email="test@example.com",
            password="SecurePass123!"
        )

        # Deactivate user
        await UsersDatabase.deactivate_user(async_session, user)
        await async_session.commit()

        # Try to login
        result = await UsersDatabase.verify_password(
            session=async_session,
            username_or_email="testuser",
            password="SecurePass123!"
        )

        assert result is None


class TestPasswordReset:
    """Test password reset functionality."""

    @pytest.mark.asyncio
    async def test_create_password_reset_token(self, async_session):
        """Test creating a password reset token."""
        # Create user
        user = await UsersDatabase.create_user(
            session=async_session,
            username="testuser",
            email="test@example.com",
            password="SecurePass123!"
        )
        await async_session.commit()

        # Create reset token
        reset_token = await UsersDatabase.create_password_reset_token(
            session=async_session,
            user=user,
            expires_in_hours=1
        )
        await async_session.commit()

        assert reset_token.token is not None
        assert len(reset_token.token) > 20
        assert reset_token.user_id == user.id
        assert reset_token.used is False
        assert reset_token.is_valid() is True

    @pytest.mark.asyncio
    async def test_use_password_reset_token(self, async_session):
        """Test using a password reset token."""
        # Create user
        user = await UsersDatabase.create_user(
            session=async_session,
            username="testuser",
            email="test@example.com",
            password="OldPass123!"
        )

        # Create reset token
        reset_token = await UsersDatabase.create_password_reset_token(
            session=async_session,
            user=user
        )
        await async_session.commit()

        # Use token to reset password
        success = await UsersDatabase.use_password_reset_token(
            session=async_session,
            reset_token=reset_token,
            new_password="NewPass123!"
        )
        await async_session.commit()

        assert success is True
        assert reset_token.used is True

        # Verify new password works
        user_check = await UsersDatabase.verify_password(
            session=async_session,
            username_or_email="testuser",
            password="NewPass123!"
        )

        assert user_check is not None

        # Verify old password doesn't work
        user_check_old = await UsersDatabase.verify_password(
            session=async_session,
            username_or_email="testuser",
            password="OldPass123!"
        )

        assert user_check_old is None

    @pytest.mark.asyncio
    async def test_use_expired_reset_token(self, async_session):
        """Test that expired tokens cannot be used."""
        # Create user
        user = await UsersDatabase.create_user(
            session=async_session,
            username="testuser",
            email="test@example.com",
            password="OldPass123!"
        )
        await async_session.commit()

        # Create token that's already expired
        reset_token = await UsersDatabase.create_password_reset_token(
            session=async_session,
            user=user,
            expires_in_hours=0
        )

        # Manually set expiration to past
        reset_token.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        await async_session.commit()

        # Try to use expired token
        success = await UsersDatabase.use_password_reset_token(
            session=async_session,
            reset_token=reset_token,
            new_password="NewPass123!"
        )

        assert success is False


class TestAuthenticationAPI:
    """Test authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_register_endpoint(self, client):
        """Test user registration endpoint."""
        response = await client.post("/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePass123!"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["user"]["username"] == "newuser"
        assert data["data"]["user"]["email"] == "newuser@example.com"
        assert "access_token" in data["data"]

        # Check that session cookie is set
        assert SESSION_COOKIE_NAME in response.cookies

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client):
        """Test that duplicate username registration fails."""
        # Register first user
        await client.post("/auth/register", json={
            "username": "testuser",
            "email": "test1@example.com",
            "password": "SecurePass123!"
        })

        # Try to register with same username
        response = await client.post("/auth/register", json={
            "username": "testuser",
            "email": "test2@example.com",
            "password": "SecurePass123!"
        })

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_endpoint(self, client):
        """Test login endpoint."""
        # Register user first
        await client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123!"
        })

        # Login
        response = await client.post("/auth/login", json={
            "username": "testuser",
            "password": "SecurePass123!"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["user"]["username"] == "testuser"
        assert "access_token" in data["data"]

    @pytest.mark.asyncio
    async def test_login_with_email(self, client):
        """Test login with email instead of username."""
        # Register user
        await client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123!"
        })

        # Login with email
        response = await client.post("/auth/login", json={
            "username": "test@example.com",
            "password": "SecurePass123!"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client):
        """Test login with wrong password."""
        # Register user
        await client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123!"
        })

        # Try to login with wrong password
        response = await client.post("/auth/login", json={
            "username": "testuser",
            "password": "WrongPassword!"
        })

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_endpoint(self, client):
        """Test logout endpoint."""
        # Register and login
        await client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123!"
        })

        # Logout
        response = await client.post("/auth/logout")

        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_get_current_user(self, client):
        """Test getting current user info."""
        # Register user
        await client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123!"
        })

        # Get current user
        response = await client.get("/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_request_password_reset(self, client):
        """Test requesting password reset."""
        # Register user
        await client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123!"
        })

        # Request password reset
        response = await client.post("/auth/request-password-reset", json={
            "email": "test@example.com"
        })

        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_reset_password_endpoint(self, client):
        """Test password reset endpoint."""
        # Register user
        await client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "OldPass123!"
        })

        # Request reset
        reset_request = await client.post("/auth/request-password-reset", json={
            "email": "test@example.com"
        })

        token = reset_request.json()["data"]["token"]

        # Reset password
        response = await client.post("/auth/reset-password", json={
            "token": token,
            "new_password": "NewPass123!"
        })

        assert response.status_code == 200
        assert response.json()["success"] is True

        # Try to login with new password
        login_response = await client.post("/auth/login", json={
            "username": "testuser",
            "password": "NewPass123!"
        })

        assert login_response.status_code == 200


# Import session cookie name from auth view
SESSION_COOKIE_NAME = "session"
