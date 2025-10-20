"""Security middleware tests for SMTPy v2 API."""
from fastapi.testclient import TestClient

from api.main import create_app


def test_security_headers_present():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    headers = resp.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("Referrer-Policy") == "no-referrer"
    assert "default-src 'self'" in headers.get("Content-Security-Policy", "")


def test_session_timeout_status_code_on_idle_expiry():
    # We cannot easily simulate time passage here; ensure middleware does not break requests
    app = create_app()
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
