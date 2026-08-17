"""Integration tests for the auth API: register, login, refresh rotation, logout."""


def test_register_creates_active_user(client, auth_factory):
    user = auth_factory.register("alice@example.com")
    assert user["email"] == "alice@example.com"
    assert user["is_active"] is True
    assert user["is_superuser"] is False
    assert "id" in user


def test_register_duplicate_email_rejected(client, auth_factory):
    auth_factory.register("bob@example.com")
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "bob@example.com",
            "password": "TestPass123",
            "full_name": "Bob Again",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Email already registered"


def test_login_returns_access_and_refresh_tokens(client, auth_factory):
    auth_factory.register("carol@example.com")
    resp = client.post(
        "/api/v1/auth/token",
        data={"username": "carol@example.com", "password": "TestPass123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


def test_login_incorrect_password_rejected(client, auth_factory):
    auth_factory.register("dave@example.com")
    resp = client.post(
        "/api/v1/auth/token",
        data={"username": "dave@example.com", "password": "wrong-password"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Incorrect email or password"


def test_refresh_rotates_token_and_revokes_previous(client, auth_factory):
    auth_factory.register("erin@example.com")
    login = client.post(
        "/api/v1/auth/token",
        data={"username": "erin@example.com", "password": "TestPass123"},
    ).json()

    rotated = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]}
    )
    assert rotated.status_code == 200
    body = rotated.json()
    assert body["access_token"]
    assert body["refresh_token"] != login["refresh_token"]

    reused = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]}
    )
    assert reused.status_code == 401


def test_logout_revokes_refresh_token(client, auth_factory):
    auth_factory.user("frank@example.com")
    login = client.post(
        "/api/v1/auth/token",
        data={"username": "frank@example.com", "password": "TestPass123"},
    ).json()

    logout = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": login["refresh_token"]},
    )
    assert logout.status_code == 204

    reused = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]}
    )
    assert reused.status_code == 401


def test_protected_endpoint_requires_auth(client):
    resp = client.get("/api/v1/orders/")
    assert resp.status_code == 401


def test_login_cleans_up_expired_refresh_tokens(client, auth_factory, db):
    from datetime import datetime, timedelta, timezone

    from app.models.refresh_token import RefreshToken

    user = auth_factory.register("token-cleanup@example.com")

    expired = RefreshToken(
        token="expired-hash-1",
        user_id=user["id"],
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        tenant_id=1,
    )
    active_old = RefreshToken(
        token="active-hash-1",
        user_id=user["id"],
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        tenant_id=1,
    )
    db.add_all([expired, active_old])
    db.commit()

    login = client.post(
        "/api/v1/auth/token",
        data={"username": "token-cleanup@example.com", "password": "TestPass123"},
    )
    assert login.status_code == 200

    remaining_hashes = {
        token.token
        for token in db.query(RefreshToken)
        .filter(RefreshToken.user_id == user["id"])
        .all()
    }
    assert "expired-hash-1" not in remaining_hashes
    assert "active-hash-1" in remaining_hashes


def test_register_rejects_weak_password(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "password": "short", "full_name": "W"},
    )
    assert resp.status_code == 422, resp.text

    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak2@example.com",
            "password": "alllettersonly",
            "full_name": "W",
        },
    )
    assert resp.status_code == 422, resp.text

    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "weak3@example.com", "password": "12345678", "full_name": "W"},
    )
    assert resp.status_code == 422, resp.text


def test_login_lockout_after_max_attempts(client, auth_factory):
    auth_factory.register("lockout@example.com", password="TestPass123")
    for _ in range(5):
        resp = client.post(
            "/api/v1/auth/token",
            data={"username": "lockout@example.com", "password": "wrongpass"},
        )
        assert resp.status_code == 400, resp.text

    # Now locked: correct password still rejected with 423
    resp = client.post(
        "/api/v1/auth/token",
        data={"username": "lockout@example.com", "password": "TestPass123"},
    )
    assert resp.status_code == 423, resp.text


def test_successful_login_resets_failed_attempts(client, auth_factory):
    auth_factory.register("reset@example.com", password="TestPass123")
    for _ in range(2):
        client.post(
            "/api/v1/auth/token",
            data={"username": "reset@example.com", "password": "wrongpass"},
        )
    # one correct login resets the counter
    resp = client.post(
        "/api/v1/auth/token",
        data={"username": "reset@example.com", "password": "TestPass123"},
    )
    assert resp.status_code == 200, resp.text
    for _ in range(4):
        resp = client.post(
            "/api/v1/auth/token",
            data={"username": "reset@example.com", "password": "wrongpass"},
        )
        assert resp.status_code == 400, resp.text
    # still not locked (5 fresh attempts needed after reset)
    resp = client.post(
        "/api/v1/auth/token",
        data={"username": "reset@example.com", "password": "TestPass123"},
    )
    assert resp.status_code == 200, resp.text


def test_auth_me_returns_profile(client, auth_factory):
    auth_factory.register("me@example.com", password="TestPass123")
    headers = auth_factory.login("me@example.com")
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["email"] == "me@example.com"
    assert body["full_name"] == "Test User"
    assert body["is_active"] is True
    assert "id" in body


def test_auth_me_requires_auth(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401 or resp.status_code == 403
