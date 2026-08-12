"""Integration tests for the sqladmin app: auth, dashboard, and reports."""

from app.core.config import settings


def _login(client, username=None, password=None):
    return client.post(
        "/admin/login",
        data={
            "username": username or settings.ADMIN_USERNAME,
            "password": password or settings.ADMIN_PASSWORD,
        },
        follow_redirects=False,
    )


def test_admin_requires_login(client):
    resp = client.get("/admin/", follow_redirects=False)
    assert resp.status_code in (302, 303)
    assert "/admin/login" in resp.headers["location"]


def test_admin_login_success_redirects(client):
    resp = _login(client)
    assert resp.status_code in (302, 303)
    assert "/admin" in resp.headers["location"]


def test_admin_login_wrong_password_rejected(client):
    resp = _login(client, password="wrong-password")
    assert resp.status_code == 400
    assert "/admin/login" in str(resp.url)


def test_admin_dashboard_renders_after_login(client):
    login = _login(client)
    assert login.status_code in (302, 303)
    resp = client.get("/admin/")
    assert resp.status_code == 200


def test_admin_reports_page_renders(client):
    _login(client)
    resp = client.get("/admin/reports")
    assert resp.status_code == 200
    assert "Reports Dashboard" in resp.text
    assert "Executive Summary" in resp.text


def test_admin_logout_clears_session(client):
    _login(client)
    resp = client.get("/admin/logout", follow_redirects=False)
    assert resp.status_code in (302, 303)
    after = client.get("/admin/", follow_redirects=False)
    assert after.status_code in (302, 303)
    assert "/admin/login" in after.headers["location"]
