"""Tests for messages module in SMTPy v2."""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from api.main import create_app
from shared.core.db import get_db
from shared.models.message import MessageStatus
from api.controllers import messages_controller
from api.database import messages_database
from api.schemas.message import MessageFilter

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
    from shared.models.base import Base
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Setup for testing
import asyncio
asyncio.run(create_test_tables())

# Create app and override dependency
app = create_app()
app.dependency_overrides[get_db] = get_test_db
client = TestClient(app)


class TestMessagesEndpoints:
    """Test messages API endpoints."""

    def test_health_check_includes_messages(self):
        """Test that health check includes messages feature."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data["features"]

    def test_list_messages_endpoint(self):
        """Test GET /messages endpoint."""
        response = client.get("/messages")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

    def test_list_messages_with_pagination(self):
        """Test messages endpoint with pagination parameters."""
        response = client.get("/messages?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_list_messages_with_filters(self):
        """Test messages endpoint with various filters."""
        # Test with status filter
        response = client.get("/messages?status=pending")
        assert response.status_code == 200

        # Test with domain filter
        response = client.get("/messages?domain_id=1")
        assert response.status_code == 200

        # Test with email filters
        response = client.get("/messages?sender_email=test@example.com")
        assert response.status_code == 200

        response = client.get("/messages?recipient_email=user@example.com")
        assert response.status_code == 200

        # Test with attachment filter
        response = client.get("/messages?has_attachments=true")
        assert response.status_code == 200

        # Test with date filters
        response = client.get("/messages?date_from=2025-01-01&date_to=2025-12-31")
        assert response.status_code == 200

    def test_search_messages_endpoint(self):
        """Test GET /messages/search endpoint."""
        response = client.get("/messages/search?q=test")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_search_messages_empty_query(self):
        """Test search with empty query parameter."""
        response = client.get("/messages/search?q=")
        assert response.status_code == 422  # Validation error for empty string

    def test_get_message_statistics(self):
        """Test GET /messages/stats endpoint."""
        response = client.get("/messages/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_messages" in data
        assert "delivered_messages" in data
        assert "failed_messages" in data
        assert "pending_messages" in data
        assert "total_size_bytes" in data

    def test_get_message_statistics_with_date(self):
        """Test message statistics with since date."""
        response = client.get("/messages/stats?since=2025-01-01")
        assert response.status_code == 200

    def test_get_message_statistics_invalid_date(self):
        """Test message statistics with invalid date format."""
        response = client.get("/messages/stats?since=invalid-date")
        assert response.status_code == 400

    def test_get_recent_messages(self):
        """Test GET /messages/recent endpoint."""
        response = client.get("/messages/recent")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_recent_messages_with_limit(self):
        """Test recent messages with custom limit."""
        response = client.get("/messages/recent?limit=5")
        assert response.status_code == 200

    def test_get_message_not_found(self):
        """Test GET /messages/{id} with non-existent message."""
        response = client.get("/messages/999999")
        assert response.status_code == 404

    def test_delete_message_not_found(self):
        """Test DELETE /messages/{id} with non-existent message."""
        response = client.delete("/messages/999999")
        assert response.status_code == 404

    def test_get_messages_by_domain_not_found(self):
        """Test GET /messages/domain/{id} with non-existent domain."""
        response = client.get("/messages/domain/999999")
        assert response.status_code == 404

    def test_get_messages_by_thread(self):
        """Test GET /messages/thread/{thread_id} endpoint."""
        response = client.get("/messages/thread/test-thread-123")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_update_message_status_not_found(self):
        """Test PATCH /messages/{id}/status with non-existent message."""
        response = client.patch("/messages/999999/status?new_status=delivered")
        assert response.status_code == 404


class TestMessageFilter:
    """Test MessageFilter schema."""

    def test_message_filter_creation(self):
        """Test creating MessageFilter with various parameters."""
        filter_obj = MessageFilter(
            domain_id=1,
            status=MessageStatus.PENDING,
            sender_email="test@example.com",
            recipient_email="user@example.com",
            has_attachments=True,
            date_from="2025-01-01",
            date_to="2025-12-31"
        )
        
        assert filter_obj.domain_id == 1
        assert filter_obj.status == MessageStatus.PENDING
        assert filter_obj.sender_email == "test@example.com"
        assert filter_obj.recipient_email == "user@example.com"
        assert filter_obj.has_attachments is True
        assert filter_obj.date_from == "2025-01-01"
        assert filter_obj.date_to == "2025-12-31"

    def test_message_filter_optional_fields(self):
        """Test MessageFilter with optional fields."""
        filter_obj = MessageFilter()
        
        assert filter_obj.domain_id is None
        assert filter_obj.status is None
        assert filter_obj.sender_email is None
        assert filter_obj.recipient_email is None
        assert filter_obj.has_attachments is None
        assert filter_obj.date_from is None
        assert filter_obj.date_to is None


@pytest.mark.asyncio
class TestMessagesController:
    """Test messages controller functions."""

    async def test_list_messages_with_filters(self, async_db: AsyncSession):
        """Test list_messages with various filters."""
        filters = MessageFilter(
            status=MessageStatus.PENDING,
            domain_id=1
        )
        
        result = await messages_controller.list_messages(
            db=async_db,
            organization_id=1,
            page=1,
            page_size=20,
            filters=filters
        )
        
        assert result.page == 1
        assert result.page_size == 20
        assert result.total >= 0
        assert isinstance(result.items, list)

    async def test_search_messages_empty_term(self, async_db: AsyncSession):
        """Test search_messages with empty search term."""
        result = await messages_controller.search_messages(
            db=async_db,
            organization_id=1,
            search_term="",
            page=1,
            page_size=20
        )
        
        assert result.total == 0
        assert len(result.items) == 0

    async def test_search_messages_valid_term(self, async_db: AsyncSession):
        """Test search_messages with valid search term."""
        result = await messages_controller.search_messages(
            db=async_db,
            organization_id=1,
            search_term="test",
            page=1,
            page_size=20
        )
        
        assert result.total >= 0
        assert isinstance(result.items, list)

    async def test_get_message_statistics(self, async_db: AsyncSession):
        """Test get_message_statistics function."""
        stats = await messages_controller.get_message_statistics(
            db=async_db,
            organization_id=1
        )
        
        assert hasattr(stats, 'total_messages')
        assert hasattr(stats, 'delivered_messages')
        assert hasattr(stats, 'failed_messages')
        assert hasattr(stats, 'pending_messages')
        assert hasattr(stats, 'total_size_bytes')
        assert stats.total_messages >= 0

    async def test_get_recent_messages(self, async_db: AsyncSession):
        """Test get_recent_messages function."""
        messages = await messages_controller.get_recent_messages(
            db=async_db,
            organization_id=1,
            limit=5
        )
        
        assert isinstance(messages, list)
        assert len(messages) <= 5

    async def test_get_message_nonexistent(self, async_db: AsyncSession):
        """Test get_message with non-existent message."""
        message = await messages_controller.get_message(
            db=async_db,
            message_id=999999,
            organization_id=1
        )
        
        assert message is None

    async def test_delete_message_nonexistent(self, async_db: AsyncSession):
        """Test delete_message with non-existent message."""
        deleted = await messages_controller.delete_message(
            db=async_db,
            message_id=999999,
            organization_id=1
        )
        
        assert deleted is False


@pytest.mark.asyncio
class TestMessagesDatabase:
    """Test messages database operations."""

    async def test_create_message(self, async_db: AsyncSession, test_domain):
        """Test creating a message in the database."""
        # Use test_domain fixture to ensure domain exists
        message = await messages_database.create_message(
            db=async_db,
            message_id="test-message-123",
            domain_id=test_domain.id,
            sender_email="sender@example.com",
            recipient_email="recipient@example.com",
            subject="Test Subject",
            body_preview="Test body preview",
            size_bytes=1024,
            has_attachments=False
        )

        assert message.message_id == "test-message-123"
        assert message.sender_email == "sender@example.com"
        assert message.recipient_email == "recipient@example.com"
        assert message.subject == "Test Subject"
        assert message.status == MessageStatus.PENDING

    async def test_get_message_by_message_id(self, async_db: AsyncSession, test_domain):
        """Test retrieving message by unique message ID."""
        # Create a test message first
        created_message = await messages_database.create_message(
            db=async_db,
            message_id="test-get-message-456",
            domain_id=test_domain.id,
            sender_email="test@example.com",
            recipient_email="user@example.com"
        )

        # Retrieve the message
        retrieved_message = await messages_database.get_message_by_message_id(
            db=async_db,
            message_id="test-get-message-456"
        )
        
        assert retrieved_message is not None
        assert retrieved_message.message_id == "test-get-message-456"
        assert retrieved_message.id == created_message.id

    async def test_update_message_status(self, async_db: AsyncSession, test_domain):
        """Test updating message status."""
        # Create a test message first
        created_message = await messages_database.create_message(
            db=async_db,
            message_id="test-update-789",
            domain_id=test_domain.id,
            sender_email="test@example.com",
            recipient_email="user@example.com"
        )
        
        # Update the status
        updated_message = await messages_database.update_message_status(
            db=async_db,
            message_id=created_message.id,
            status=MessageStatus.DELIVERED,
            forwarded_to="forwarded@example.com"
        )
        
        assert updated_message is not None
        assert updated_message.status == MessageStatus.DELIVERED
        assert updated_message.forwarded_to == "forwarded@example.com"

    async def test_get_message_stats_by_organization(self, async_db: AsyncSession):
        """Test getting message statistics by organization."""
        stats = await messages_database.get_message_stats_by_organization(
            db=async_db,
            organization_id=1
        )
        
        assert "total_messages" in stats
        assert "delivered_messages" in stats
        assert "failed_messages" in stats
        assert "pending_messages" in stats
        assert "total_size_bytes" in stats
        assert "status_breakdown" in stats
        
        assert stats["total_messages"] >= 0
        assert isinstance(stats["status_breakdown"], dict)

    async def test_search_messages(self, async_db: AsyncSession, test_domain):
        """Test searching messages."""
        # Create a test message with searchable content
        await messages_database.create_message(
            db=async_db,
            message_id="searchable-message-123",
            domain_id=test_domain.id,
            sender_email="searchable@example.com",
            recipient_email="recipient@example.com",
            subject="Searchable Subject"
        )
        
        # Search for the message
        results = await messages_database.search_messages(
            db=async_db,
            organization_id=1,
            search_term="searchable",
            skip=0,
            limit=10
        )
        
        assert isinstance(results, list)
        # Note: Results might be empty due to test database isolation
        # but the function should not raise errors

    async def test_get_messages_by_thread(self, async_db: AsyncSession, test_domain):
        """Test getting messages by thread ID."""
        thread_id = "test-thread-456"

        # Create test messages in the same thread
        await messages_database.create_message(
            db=async_db,
            message_id="thread-msg-1",
            domain_id=test_domain.id,
            sender_email="sender1@example.com",
            recipient_email="recipient@example.com",
            thread_id=thread_id
        )

        await messages_database.create_message(
            db=async_db,
            message_id="thread-msg-2",
            domain_id=test_domain.id,
            sender_email="sender2@example.com",
            recipient_email="recipient@example.com",
            thread_id=thread_id
        )
        
        # Get messages by thread
        thread_messages = await messages_database.get_messages_by_thread(
            db=async_db,
            thread_id=thread_id,
            organization_id=1
        )
        
        assert isinstance(thread_messages, list)
        # All messages should have the same thread_id
        for message in thread_messages:
            assert message.thread_id == thread_id