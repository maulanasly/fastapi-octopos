"""Multi-tenant isolation tests.

Each ``multi_tenant_mode`` test registers real tenants (one per signup)
instead of the shared "default" tenant, then asserts data created by one
tenant is invisible to another and that cross-tenant access is denied.
"""
import _tenant_mode
import pytest


@pytest.fixture(autouse=True)
def multi_tenant_mode():
    """Register real tenants (one per signup) for every test in this module."""
    _tenant_mode.FORCE_DEFAULT_TENANT = False
    yield
    _tenant_mode.FORCE_DEFAULT_TENANT = True


def _manager_headers(auth_factory, assign_role, email):
    user = auth_factory.register(email)
    assign_role(user["id"], "manager")
    return auth_factory.login(email)


@pytest.fixture()
def manager_a(auth_factory, assign_role):
    return _manager_headers(auth_factory, assign_role, "manager-a@example.com")


@pytest.fixture()
def manager_b(auth_factory, assign_role):
    return _manager_headers(auth_factory, assign_role, "manager-b@example.com")


@pytest.fixture()
def tenant_a(auth_factory):
    return auth_factory.user("tenant-a@example.com")


@pytest.fixture()
def tenant_b(auth_factory):
    return auth_factory.user("tenant-b@example.com")


def _order_payload(product_id):
    return {"items": [{"product_id": product_id, "quantity": 1}]}


def test_new_tenant_register_grants_owner_role(auth_factory, db):
    from app.models.user import User

    user = auth_factory.register("owner@example.com")
    roles = [role.name for role in db.get(User, user["id"]).roles]
    assert "admin" in roles
    assert "cashier" in roles


def test_products_isolated_between_tenants(client, make_product, manager_a, manager_b):
    product = make_product(manager_a, name="A-only", sku="SKU-A")

    list_resp = client.get("/api/v1/products", headers=manager_b)
    assert list_resp.status_code == 200
    assert list_resp.json() == []

    for method, kwargs in (("put", {"json": {}}), ("delete", {})):
        resp = getattr(client, method)(
            f"/api/v1/products/{product['id']}", headers=manager_b, **kwargs
        )
        assert resp.status_code == 404, f"{method} leaked cross-tenant product"


def test_categories_isolated_between_tenants(
    client, manager_a, manager_b, make_product
):
    make_product(manager_a, name="CatA", sku="SKU-CAT-A")

    resp = client.get("/api/v1/products/categories", headers=manager_b)
    assert resp.status_code == 200
    assert resp.json() == []


def test_same_sku_allowed_across_tenants(client, make_product, manager_a, manager_b):
    a_product = make_product(manager_a, name="A copy", sku="SHARED-SKU")
    b_product = make_product(manager_b, name="B copy", sku="SHARED-SKU")

    assert a_product["id"] != b_product["id"]
    b_list = client.get("/api/v1/products", headers=manager_b).json()
    assert [p["id"] for p in b_list] == [b_product["id"]]


def test_same_email_registers_second_tenant_and_login_ambiguous(client, auth_factory):
    for tenant_user in (
        auth_factory.register("dup@example.com"),
        auth_factory.register("dup@example.com"),
    ):
        assert tenant_user["email"] == "dup@example.com"

    resp = client.post(
        "/api/v1/auth/token",
        data={"username": "dup@example.com", "password": "TestPass123"},
    )
    assert resp.status_code == 400
    assert "Multiple accounts" in resp.json()["detail"]


def test_orders_isolated_between_tenants(
    client, make_product, open_drawer, manager_a, manager_b
):
    product = make_product(manager_a, name="Orderable", sku="SKU-ORD-A")
    open_drawer(manager_a, starting_cash=100.0)

    order_resp = client.post(
        "/api/v1/orders",
        headers=manager_a,
        json=_order_payload(product["id"]),
    )
    assert order_resp.status_code == 200, order_resp.text
    order = order_resp.json()

    assert client.get("/api/v1/orders", headers=manager_b).json() == []

    receipt = client.get(f"/api/v1/orders/{order['id']}/receipt", headers=manager_b)
    assert receipt.status_code == 404, "tenant B read tenant A's order receipt"

    blocked = client.post(
        "/api/v1/orders", headers=manager_b, json=_order_payload(product["id"])
    )
    assert blocked.status_code == 404, "tenant B created an order with A's product"


def test_customers_isolated_between_tenants(client, tenant_a, tenant_b):
    create = client.post(
        "/api/v1/customers",
        headers=tenant_a,
        json={"name": "Alice", "phone": "+1-555-0100"},
    )
    assert create.status_code == 200, create.text
    customer_id = create.json()["id"]

    assert client.get("/api/v1/customers", headers=tenant_b).json() == []
    resp = client.get(f"/api/v1/customers/{customer_id}", headers=tenant_b)
    assert resp.status_code == 404


def test_promotions_isolated_between_tenants(client, manager_a, manager_b):
    for headers in (manager_a, manager_b):
        resp = client.post(
            "/api/v1/promotions",
            headers=headers,
            json={
                "name": "Flat Ten",
                "code": "FLAT10",
                "discount_type": "percentage",
                "discount_value": 10,
            },
        )
        assert resp.status_code == 200, resp.text

    a_list = client.get("/api/v1/promotions", headers=manager_a).json()
    b_list = client.get("/api/v1/promotions", headers=manager_b).json()
    assert len(a_list) == 1 and len(b_list) == 1
    assert a_list[0]["id"] != b_list[0]["id"]


def test_audit_logs_are_tenant_scoped(client, db, tenant_a, tenant_b):
    from app.core.audit import log_action
    from app.models.audit_log import AuditLog
    from app.models.user import User

    user_a = db.query(User).filter(User.email == "tenant-a@example.com").one()
    log_action(
        db=db,
        action="test.isolation",
        user_id=user_a.id,
        resource_type="product",
        resource_id=1,
    )
    db.commit()

    rows = db.query(AuditLog).all()
    assert len(rows) == 1
    assert rows[0].tenant_id == user_a.tenant_id
    assert rows[0].tenant_id != (
        db.query(User.tenant_id).filter(User.email == "tenant-b@example.com").scalar()
    )
