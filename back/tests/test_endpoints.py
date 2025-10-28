"""Comprehensive endpoint tests for SMTPy v2 API."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from api.main import create_app
from shared.core.db import get_db

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


# --- Health Endpoints ---
def test_root_health():
    """Test root health endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "SMTPy v2 API"


def test_detailed_health():
    """Test detailed health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "2.0.0"
    assert "domains" in data["features"]
    assert "messages" in data["features"]
    assert "billing" in data["features"]


# --- Domain Endpoints ---
def test_create_domain():
    """Test POST /domains."""
    response = client.post(
        "/domains",
        json={"name": "test.example.com"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test.example.com"
    assert data["status"] == "pending"
    assert data["is_active"] is True


def test_create_domain_duplicate():
    """Test creating duplicate domain fails."""
    # First creation should succeed
    response1 = client.post(
        "/domains",
        json={"name": "duplicate.example.com"}
    )
    assert response1.status_code == 201
    
    # Second creation should fail
    response2 = client.post(
        "/domains",
        json={"name": "duplicate.example.com"}
    )
    assert response2.status_code == 400


def test_list_domains():
    """Test GET /domains."""
    response = client.get("/domains")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data


def test_list_domains_with_pagination():
    """Test GET /domains with pagination."""
    response = client.get("/domains?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 5


def test_get_domain_not_found():
    """Test GET /domains/{id} with non-existent domain."""
    response = client.get("/domains/999999")
    assert response.status_code == 404


def test_update_domain_not_found():
    """Test PATCH /domains/{id} with non-existent domain."""
    response = client.patch(
        "/domains/999999",
        json={"is_active": False}
    )
    assert response.status_code == 404


def test_delete_domain_not_found():
    """Test DELETE /domains/{id} with non-existent domain."""
    response = client.delete("/domains/999999")
    assert response.status_code == 404


def test_verify_domain_not_found():
    """Test POST /domains/{id}/verify with non-existent domain."""
    response = client.post("/domains/999999/verify")
    assert response.status_code == 404


def test_get_dns_records_not_found():
    """Test GET /domains/{id}/dns-records with non-existent domain."""
    response = client.get("/domains/999999/dns-records")
    assert response.status_code == 404


# --- Message Endpoints ---
def test_list_messages():
    """Test GET /messages."""
    response = client.get("/messages")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_search_messages():
    """Test GET /messages/search."""
    response = client.get("/messages/search?q=test")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_search_messages_empty_query():
    """Test search with empty query fails validation."""
    response = client.get("/messages/search?q=")
    assert response.status_code == 422


def test_get_message_stats():
    """Test GET /messages/stats."""
    response = client.get("/messages/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_messages" in data
    assert "delivered_messages" in data
    assert "failed_messages" in data


def test_get_recent_messages():
    """Test GET /messages/recent."""
    response = client.get("/messages/recent")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_message_not_found():
    """Test GET /messages/{id} with non-existent message."""
    response = client.get("/messages/999999")
    assert response.status_code == 404


def test_delete_message_not_found():
    """Test DELETE /messages/{id} with non-existent message."""
    response = client.delete("/messages/999999")
    assert response.status_code == 404


# --- Billing Endpoints ---
@pytest.mark.asyncio
async def test_create_checkout_session(authenticated_client):
    """Test POST /billing/checkout-session with authentication."""
    from unittest.mock import patch, AsyncMock

    with patch('api.services.stripe_service.create_or_get_customer', new_callable=AsyncMock) as mock_customer, \
         patch('api.services.stripe_service.create_checkout_session', new_callable=AsyncMock) as mock_checkout:

        mock_customer.return_value = "cus_test_123"
        mock_checkout.return_value = {
            "url": "https://checkout.stripe.com/test",
            "session_id": "cs_test_123"
        }

        response = await authenticated_client.post(
            "/billing/checkout-session",
            json={"price_id": "price_test_123"}
        )

        assert response.status_code == 201
        assert "url" in response.json()
        assert "session_id" in response.json()


@pytest.mark.asyncio
async def test_get_customer_portal(authenticated_client):
    """Test GET /billing/customer-portal with authentication."""
    response = await authenticated_client.get("/billing/customer-portal")
    # This will fail with 400/404 because no customer exists
    assert response.status_code in [200, 400, 404]


def test_get_subscription():
    """Test GET /subscriptions/me."""
    response = client.get("/subscriptions/me")
    # This will return 404 because no subscription exists
    assert response.status_code == 404


def test_cancel_subscription_no_subscription():
    """Test PATCH /subscriptions/cancel with no subscription."""
    response = client.patch(
        "/subscriptions/cancel",
        json={"cancel_at_period_end": True}
    )
    # Should return 400/404 because no subscription exists
    assert response.status_code in [400, 404]


def test_resume_subscription_no_subscription():
    """Test PATCH /subscriptions/resume with no subscription."""
    response = client.patch("/subscriptions/resume")
    # Should return 400/404 because no subscription exists
    assert response.status_code in [400, 404]


@pytest.mark.asyncio
async def test_get_organization_billing(authenticated_client):
    """Test GET /billing/organization with authentication."""
    response = await authenticated_client.get("/billing/organization")
    # Should return 404 or 200 (depending on if org billing info exists)
    assert response.status_code in [200, 404]


def test_stripe_webhook_missing_signature():
    """Test POST /webhooks/stripe without signature."""
    response = client.post(
        "/webhooks/stripe",
        json={"type": "test.event"}
    )
    # The webhook endpoint returns 500 when signature is missing (which is caught by exception handler)
    assert response.status_code == 500
