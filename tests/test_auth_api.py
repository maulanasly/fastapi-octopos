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
