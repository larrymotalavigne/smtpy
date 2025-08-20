from fastapi.testclient import TestClient

from api.main import create_app

client = TestClient(create_app())


def test_landing_page():
    """Test that the landing page loads"""
    response = client.get("/")
    assert response.status_code == 200


def test_admin_redirect_when_not_logged_in():
    """Test that admin redirects to login when not authenticated"""
    response = client.get("/admin", follow_redirects=False)
    assert response.status_code == 303
    assert "/login" in response.headers["location"]


def test_dashboard_redirect_when_not_logged_in():
    """Test that dashboard redirects to login when not authenticated"""
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 303
    assert "/login" in response.headers["location"]


def test_api_dns_check():
    """Test DNS check API endpoint"""
    response = client.get("/api/dns-check?domain=example.com")
    assert response.status_code == 200
    data = response.json()
    assert "spf" in data
    assert "dkim" in data
    assert "dmarc" in data
