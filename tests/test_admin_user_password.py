"""Admin panel user creation must hash passwords; blank keeps the hash."""

from app.core.security import verify_password
from app.models.user import User


def _login(client):
    from app.core.config import settings

    resp = client.post(
        "/admin/login",
        data={
            "username": settings.ADMIN_USERNAME,
            "password": settings.ADMIN_PASSWORD,
        },
    )
    assert resp.status_code in (302, 200), resp.text
    return client


def _create_user(client, email, password="", full_name="Panel User"):
    data = {
        "email": email,
        "full_name": full_name,
        "is_active": "True",
        "hashed_password": password,
    }
    return client.post("/admin/user/create", data=data)


def test_admin_create_user_hashes_password(client, db):
    _login(client)
    resp = _create_user(client, "panel@example.com", password="PanelPass123")
    assert resp.status_code in (302, 200), resp.text

    user = db.query(User).filter(User.email == "panel@example.com").one()
    assert user.hashed_password.startswith("$2"), (
        "stored password must be a bcrypt hash, got: %s" % user.hashed_password
    )
    assert user.hashed_password != "PanelPass123"
    assert verify_password("PanelPass123", user.hashed_password)


def test_admin_create_user_without_password_allowed(client, db):
    _login(client)
    resp = _create_user(client, "nopass@example.com")
    assert resp.status_code in (302, 200), resp.text

    user = db.query(User).filter(User.email == "nopass@example.com").one()
    assert user.hashed_password is None


def test_admin_edit_user_rehashes_new_password(client, db):
    _login(client)
    _create_user(client, "edit@example.com", password="OldPass123")
    user = db.query(User).filter(User.email == "edit@example.com").one()
    old_hash = user.hashed_password

    resp = client.post(
        f"/admin/user/edit/{user.id}",
        data={
            "email": "edit@example.com",
            "full_name": "Edited",
            "is_active": "True",
            "hashed_password": "NewPass456",
        },
    )
    assert resp.status_code in (302, 200), resp.text

    db.expire_all()
    user = db.query(User).filter(User.email == "edit@example.com").one()
    assert user.hashed_password != old_hash
    assert verify_password("NewPass456", user.hashed_password)


def test_admin_edit_user_blank_password_keeps_hash(client, db):
    _login(client)
    _create_user(client, "keep@example.com", password="KeepPass123")
    user = db.query(User).filter(User.email == "keep@example.com").one()
    old_hash = user.hashed_password

    resp = client.post(
        f"/admin/user/edit/{user.id}",
        data={
            "email": "keep@example.com",
            "full_name": "Kept",
            "is_active": "True",
            "hashed_password": "",
        },
    )
    assert resp.status_code in (302, 200), resp.text

    db.expire_all()
    user = db.query(User).filter(User.email == "keep@example.com").one()
    assert user.hashed_password == old_hash
    assert verify_password("KeepPass123", user.hashed_password)


def test_admin_created_user_can_login_via_api(client, db):
    _login(client)
    _create_user(client, "panel-login@example.com", password="PanelPass123")
    resp = client.post(
        "/api/v1/auth/token",
        data={
            "username": "panel-login@example.com",
            "password": "PanelPass123",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["access_token"]
