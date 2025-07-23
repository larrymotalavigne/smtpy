import pytest
from fastapi.testclient import TestClient
from main import create_app

client = TestClient(create_app())

# --- Public endpoints ---
def test_root():
    r = client.get("/")
    assert r.status_code == 200

def test_landing():
    r = client.get("/", headers={"accept": "text/html"})
    assert r.status_code == 200

def test_login_get():
    r = client.get("/login")
    assert r.status_code == 200

def test_register_get():
    r = client.get("/register")
    assert r.status_code == 200

def test_forgot_password_get():
    r = client.get("/forgot-password")
    assert r.status_code == 200

def test_dashboard_requires_login():
    r = client.get("/dashboard", follow_redirects=False)
    assert r.status_code == 303
    assert "/login" in r.headers["location"]

def test_admin_requires_login():
    r = client.get("/admin", follow_redirects=False)
    assert r.status_code == 303
    assert "/login" in r.headers["location"]

def test_invite_user_requires_admin():
    r = client.get("/invite-user", follow_redirects=False)
    assert r.status_code in (303, 403)

def test_users_requires_admin():
    r = client.get("/users", follow_redirects=False)
    assert r.status_code in (303, 403)

def test_api_dns_check():
    r = client.get("/api/dns-check?domain=example.com")
    assert r.status_code == 200
    data = r.json()
    assert "spf" in data and "dkim" in data and "dmarc" in data

def test_api_activity_stats():
    r = client.get("/api/activity-stats")
    assert r.status_code == 200

def test_dkim_public_key():
    r = client.get("/dkim-public-key?domain=example.com")
    assert r.status_code == 200
    assert "DKIM public key" in r.text or "not found" in r.text

def test_domain_dns_requires_login():
    r = client.get("/domain-dns/1", follow_redirects=False)
    assert r.status_code in (303, 403)

def test_domain_aliases_requires_login():
    r = client.get("/domain-aliases/1", follow_redirects=False)
    assert r.status_code in (303, 403)

def test_api_aliases_requires_login():
    r = client.get("/api/aliases/1", follow_redirects=False)
    assert r.status_code in (303, 403, 404)

def test_api_alias_add_requires_login():
    import datetime
    expires = datetime.datetime.now().isoformat()
    r = client.post("/api/aliases/1", json={"local_part": "test", "targets": "test@example.com", "expires_at": expires}, follow_redirects=False)
    assert r.status_code in (303, 403, 404)

def test_api_alias_delete_requires_login():
    r = client.delete("/api/alias/1", follow_redirects=False)
    assert r.status_code in (303, 403, 404)

def test_api_alias_test_requires_login():
    r = client.post("/api/alias-test/1", follow_redirects=False)
    assert r.status_code in (303, 403, 404)

def test_add_domain_requires_login():
    r = client.post("/add-domain", data={"name": "example.com"}, follow_redirects=False)
    assert r.status_code in (303, 403)

def test_delete_domain_requires_login():
    r = client.post("/delete-domain", data={"domain_id": 1}, follow_redirects=False)
    assert r.status_code in (303, 403)

def test_add_alias_requires_login():
    r = client.post("/add-alias", data={"local_part": "test", "target": "test@example.com", "domain_id": 1}, follow_redirects=False)
    assert r.status_code in (303, 403)

def test_delete_alias_requires_login():
    r = client.post("/delete-alias", data={"alias_id": 1}, follow_redirects=False)
    assert r.status_code in (303, 403)

def test_edit_catchall_requires_login():
    r = client.post("/edit-catchall", data={"domain_id": 1, "catch_all": "test@example.com"}, follow_redirects=False)
    assert r.status_code in (303, 403)

def test_users_edit_requires_admin():
    r = client.post("/users/edit", data={"user_id": 1, "email": "test@example.com", "role": "user"}, follow_redirects=False)
    assert r.status_code in (303, 403)

def test_users_delete_requires_admin():
    r = client.post("/users/delete", data={"user_id": 1}, follow_redirects=False)
    assert r.status_code in (303, 403)

def test_register_post_duplicate():
    # Try to register with an existing username/email (should fail if already exists)
    r = client.post("/register", data={"username": "admin", "email": "admin@example.com", "password": "password"})
    assert r.status_code == 200
    # Should show error in response
    assert "already" in r.text or "exists" in r.text or "Check your email" in r.text 