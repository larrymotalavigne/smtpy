"""Initial functional tests mapped from users.feature scenarios.

These tests intentionally avoid external integrations and database dependencies.
"""
from fastapi.testclient import TestClient

from api.main import create_app


def _client():
    app = create_app()
    return TestClient(app)


def test_landing_page_available():
    # When I visit the root URL
    client = _client()
    resp = client.get("/")

    # Then I receive a successful response
    assert resp.status_code == 200

    # And I can see the API documentation (FastAPI SwaggerUI or ReDoc snippet)
    text = resp.text.lower()
    assert "swagger" in text or "openapi" in text or "redoc" in text


def test_health_endpoint_reports_healthy():
    # When I request the health endpoint
    client = _client()
    resp = client.get("/health")

    # Then I receive a successful response
    assert resp.status_code == 200

    # And the health payload indicates the service is healthy
    payload = resp.json()
    assert payload.get("status") == "healthy"
    assert payload.get("service")
    assert payload.get("version")


def test_unknown_route_returns_not_found():
    # When I visit an unknown URL
    client = _client()
    resp = client.get("/this-route-does-not-exist")

    # Then I receive a not found response
    assert resp.status_code == 404
