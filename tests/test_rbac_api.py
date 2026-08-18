"""Integration tests for RBAC enforcement and management at the API layer."""

from conftest import order_payload


def test_new_user_gets_default_cashier_role(client, auth_factory):
    user = auth_factory.register("roles@example.com")
    assert user["is_superuser"] is False


def test_cashier_cannot_create_product(client, cashier_headers):
    resp = client.post(
        "/api/v1/products",
        headers=cashier_headers,
        json={"name": "Nope", "sku": "SKU-NOPE", "price": 1.0, "stock_quantity": 1},
    )
    assert resp.status_code == 403


def test_manager_can_create_product(client, manager_headers, make_product):
    product = make_product(manager_headers, name="Manager Item", sku="SKU-MGR")
    assert product["name"] == "Manager Item"
    assert product["stock_quantity"] == 10


def test_permissions_endpoint_reflects_role(client, auth_factory, assign_role):
    cashier = auth_factory.user("perm-cashier@example.com")
    resp = client.get("/api/v1/rbac/me/permissions", headers=cashier)
    assert resp.status_code == 200
    assert "products:manage" not in resp.json()["permissions"]

    manager = auth_factory.register("perm-manager@example.com")
    assign_role(manager["id"], "manager")
    manager_headers = auth_factory.login("perm-manager@example.com")
    resp = client.get("/api/v1/rbac/me/permissions", headers=manager_headers)
    assert "products:manage" in resp.json()["permissions"]


def test_payment_on_other_users_order_forbidden(
    client,
    auth_factory,
    make_product,
    open_drawer,
    manager_headers,
):
    product = make_product(
        manager_headers, name="Paid Item", sku="SKU-PAID", price=50.0
    )
    cashier_a = auth_factory.user("cashier-a@example.com")
    open_drawer(cashier_a)
    order = client.post(
        "/api/v1/orders/",
        headers=cashier_a,
        json=order_payload(product["id"], quantity=2),
    )
    assert order.status_code == 200, order.text

    cashier_b = auth_factory.user("cashier-b@example.com")
    resp = client.post(
        f"/api/v1/orders/{order.json()['id']}/payments",
        headers=cashier_b,
        json={"payment_method": "cash", "amount": 100.0},
    )
    assert resp.status_code == 403


def test_order_listing_scoped_to_owner(
    client, auth_factory, make_product, open_drawer, manager_headers
):
    product = make_product(
        manager_headers, name="Scoped Item", sku="SKU-SCOPE", price=10.0
    )
    cashier_a = auth_factory.user("scope-a@example.com")
    open_drawer(cashier_a)
    client.post("/api/v1/orders/", headers=cashier_a, json=order_payload(product["id"]))

    cashier_b = auth_factory.user("scope-b@example.com")
    open_drawer(cashier_b)
    client.post("/api/v1/orders/", headers=cashier_b, json=order_payload(product["id"]))

    owned = client.get("/api/v1/orders/", headers=cashier_a)
    assert owned.status_code == 200
    orders = owned.json()
    assert len(orders) == 1
    assert orders[0]["user_id"] is not None


def _admin_headers(client, auth_factory, assign_role):
    user = auth_factory.register("admin@example.com")
    assign_role(user["id"], "admin")
    return auth_factory.login("admin@example.com")


def test_cashier_cannot_manage_roles(client, cashier_headers):
    resp = client.get("/api/v1/rbac/roles", headers=cashier_headers)
    assert resp.status_code == 403


def test_seeded_roles_listed(client, auth_factory, assign_role):
    admin = _admin_headers(client, auth_factory, assign_role)
    resp = client.get("/api/v1/rbac/roles", headers=admin)
    assert resp.status_code == 200, resp.text
    names = {role["name"] for role in resp.json()}
    assert {"cashier", "manager", "admin"} <= names


def test_create_custom_role_with_permissions(client, auth_factory, assign_role):
    admin = _admin_headers(client, auth_factory, assign_role)
    resp = client.post(
        "/api/v1/rbac/roles",
        headers=admin,
        json={
            "name": "viewer",
            "description": "Read-only",
            "permission_codes": ["reports:view"],
        },
    )
    assert resp.status_code == 200, resp.text
    role = resp.json()
    assert role["is_system"] is False
    assert {p["code"] for p in role["permissions"]} == {"reports:view"}


def test_create_role_with_unknown_permission_404(client, auth_factory, assign_role):
    admin = _admin_headers(client, auth_factory, assign_role)
    resp = client.post(
        "/api/v1/rbac/roles",
        headers=admin,
        json={"name": "broken", "permission_codes": ["reports:view", "nope:manage"]},
    )
    assert resp.status_code == 404
    assert "nope:manage" in resp.json()["detail"]


def test_assign_role_grants_permissions(client, auth_factory, assign_role):
    admin = _admin_headers(client, auth_factory, assign_role)
    role = client.post(
        "/api/v1/rbac/roles",
        headers=admin,
        json={"name": "analyst", "permission_codes": ["reports:view"]},
    ).json()

    target = auth_factory.register("analyst@example.com")
    assigned = client.post(
        f"/api/v1/rbac/users/{target['id']}/roles",
        headers=admin,
        json={"role_ids": [role["id"]]},
    )
    assert assigned.status_code == 200, assigned.text
    assert assigned.json()["user_id"] == target["id"]

    analyst_headers = auth_factory.login("analyst@example.com")
    perms = client.get("/api/v1/rbac/me/permissions", headers=analyst_headers).json()
    assert "reports:view" in perms["permissions"]
    assert "products:manage" not in perms["permissions"]

    report = client.get("/api/v1/reports/sales", headers=analyst_headers)
    assert report.status_code == 200


def test_assign_missing_role_404(client, auth_factory, assign_role):
    admin = _admin_headers(client, auth_factory, assign_role)
    target = auth_factory.register("norole@example.com")
    resp = client.post(
        f"/api/v1/rbac/users/{target['id']}/roles",
        headers=admin,
        json={"role_ids": [99999]},
    )
    assert resp.status_code == 404


def test_superuser_gets_all_permissions(client, auth_factory, db):
    user = auth_factory.register("supreme@example.com")
    from app.models.user import User

    with db.begin():
        db_user = db.get(User, user["id"])
        db_user.is_superuser = True

    headers = auth_factory.login("supreme@example.com")
    perms = client.get("/api/v1/rbac/me/permissions", headers=headers).json()
    assert "settings:manage" in perms["permissions"]
    assert "users:manage_roles" in perms["permissions"]


def test_permissions_catalog_lists_definitions(client, manager_headers):
    resp = client.get("/api/v1/rbac/permissions", headers=manager_headers)
    assert resp.status_code == 200, resp.text
    codes = {p["code"] for p in resp.json()}
    assert "products:manage" in codes
    assert "users:manage_roles" in codes


def test_users_list_requires_users_manage(client, auth_factory, cashier_headers):
    auth_factory.register("user-list@example.com")
    resp = client.get("/api/v1/users/", headers=cashier_headers)
    assert resp.status_code == 403  # permission-gated staff listing

    owner = auth_factory.register("owner2@example.com")
    from conftest import SessionLocal

    from app.models.user import User

    db = SessionLocal()
    user = db.get(User, owner["id"])
    user.is_superuser = True
    db.commit()
    db.close()

    from app.core.limiter import limiter

    limiter.enabled = False
    resp2 = client.post(
        "/api/v1/auth/token",
        data={"username": "owner2@example.com", "password": "TestPass123"},
    )
    headers = {"Authorization": f"Bearer {resp2.json()['access_token']}"}
    resp = client.get("/api/v1/users/", headers=headers)
    assert resp.status_code == 200, resp.text
    emails = {u_["email"] for u_ in resp.json()}
    assert "user-list@example.com" in emails


def test_staff_create_update_deactivate_flow(client, auth_factory, assign_role):
    admin_user = auth_factory.register("staff-admin@example.com")
    assign_role(admin_user["id"], "admin")
    admin_headers = auth_factory.login("staff-admin@example.com")

    created = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "email": "staff-1@example.com",
            "full_name": "Staff One",
            "password": "TestPass123",
            "is_active": True,
        },
    )
    assert created.status_code == 201, created.text
    staff = created.json()
    assert staff["is_superuser"] is False
    assert staff["tenant_id"] == admin_user["tenant_id"]
    assert {"cashier"} == {r["name"] for r in staff["roles"]}

    updated = client.put(
        f"/api/v1/users/{staff['id']}",
        headers=admin_headers,
        json={"full_name": "Staff Renamed", "is_active": False},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["full_name"] == "Staff Renamed"
    assert updated.json()["is_active"] is False

    list_resp = client.get("/api/v1/users", headers=admin_headers)
    assert list_resp.status_code == 200, list_resp.text
    emails = {u_["email"] for u_ in list_resp.json()}
    assert "staff-1@example.com" in emails
    assert "staff-admin@example.com" in emails


def test_staff_create_duplicate_email_400(client, auth_factory, assign_role):
    admin_user = auth_factory.register("staff-dup-admin@example.com")
    assign_role(admin_user["id"], "admin")
    admin_headers = auth_factory.login("staff-dup-admin@example.com")

    payload = {
        "email": "staff-dup@example.com",
        "full_name": "Dup",
        "password": "TestPass123",
    }
    first = client.post("/api/v1/users", headers=admin_headers, json=payload)
    assert first.status_code == 201, first.text
    second = client.post("/api/v1/users", headers=admin_headers, json=payload)
    assert second.status_code == 400


def test_staff_password_reset(client, auth_factory, assign_role):
    admin_user = auth_factory.register("staff-pw-admin@example.com")
    assign_role(admin_user["id"], "admin")
    admin_headers = auth_factory.login("staff-pw-admin@example.com")

    staff = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "email": "staff-pw@example.com",
            "full_name": "PW",
            "password": "OldPass123",
        },
    ).json()

    resp = client.put(
        f"/api/v1/users/{staff['id']}",
        headers=admin_headers,
        json={"password": "NewPass456"},
    )
    assert resp.status_code == 200, resp.text

    from app.core.limiter import limiter

    limiter.enabled = False
    login = client.post(
        "/api/v1/auth/token",
        data={"username": "staff-pw@example.com", "password": "NewPass456"},
    )
    assert login.status_code == 200, login.text
    assert client.post(
        "/api/v1/auth/token",
        data={"username": "staff-pw@example.com", "password": "OldPass123"},
    ).status_code in (400, 401)


def test_admin_cannot_deactivate_self(client, auth_factory, assign_role):
    admin_user = auth_factory.register("staff-self@example.com")
    assign_role(admin_user["id"], "admin")
    admin_headers = auth_factory.login("staff-self@example.com")

    resp = client.put(
        f"/api/v1/users/{admin_user['id']}",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert resp.status_code == 400


def test_cashier_cannot_manage_staff(client, auth_factory, cashier_headers):
    resp = client.post(
        "/api/v1/users",
        headers=cashier_headers,
        json={
            "email": "nope-staff@example.com",
            "full_name": "Nope",
            "password": "TestPass123",
        },
    )
    assert resp.status_code == 403
