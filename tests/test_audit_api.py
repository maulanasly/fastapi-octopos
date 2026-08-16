"""Tests for the audit log endpoint and hook coverage."""

from fastapi.testclient import TestClient

from app.models.user import User


def _superuser_headers(client, db):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "audit-owner@example.com",
            "password": "TestPass123",
            "full_name": "Owner",
        },
    )
    resp = client.post(
        "/api/v1/auth/token",
        data={
            "username": "audit-owner@example.com",
            "password": "TestPass123",
        },
    )
    assert resp.status_code == 200, resp.text
    owner = db.query(User).filter(User.email == "audit-owner@example.com").one()
    owner.is_superuser = True
    db.commit()
    resp = client.post(
        "/api/v1/auth/token",
        data={
            "username": "audit-owner@example.com",
            "password": "TestPass123",
        },
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_audit_logs_require_superuser(client: TestClient, db):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "audit-cashier@example.com",
            "password": "TestPass123",
            "full_name": "Cashier",
        },
    )
    resp = client.post(
        "/api/v1/auth/token",
        data={
            "username": "audit-cashier@example.com",
            "password": "TestPass123",
        },
    )
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    resp = client.get("/api/v1/audit/logs", headers=headers)
    assert resp.status_code == 400, resp.text


def test_refund_records_audit_entry(client: TestClient, db):
    # seed catalog
    headers = _superuser_headers(client, db)
    cat = client.post(
        "/api/v1/products/categories", headers=headers, json={"name": "AuditCat"}
    ).json()
    product = client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "name": "Audit Product",
            "sku": "AUD-1",
            "price": 5.0,
            "stock_quantity": 10,
            "category_id": cat["id"],
        },
    )
    assert product.status_code == 200, product.text
    product = product.json()
    client.post("/api/v1/drawers/open", headers=headers, json={"starting_cash": 0.0})
    order = client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "items": [{"product_id": product["id"], "quantity": 1}],
        },
    )
    assert order.status_code == 200, order.text
    order = order.json()
    client.post(
        f"/api/v1/orders/{order['id']}/payments",
        headers=headers,
        json={"payment_method": "cash", "amount": 10.0},
    )
    refund = client.post(
        "/api/v1/refunds",
        headers=headers,
        json={
            "order_id": order["id"],
            "items": [{"order_item_id": order["items"][0]["id"], "quantity": 1}],
        },
    )
    assert refund.status_code == 200, refund.text

    resp = client.get("/api/v1/audit/logs?action=refund.create", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] >= 1
    entry = body["items"][0]
    assert entry["action"] == "refund.create"
    assert entry["resource_type"] == "refund"
    assert entry["details_json"] is not None


def test_rbac_and_reconcile_record_audit_entries(client: TestClient, db):
    headers = _superuser_headers(client, db)
    user = client.post(
        "/api/v1/auth/register",
        json={
            "email": "audit-victim@example.com",
            "password": "TestPass123",
            "full_name": "Victim",
        },
    ).json()
    roles = client.get("/api/v1/rbac/roles", headers=headers).json()
    role_ids = [r["id"] for r in roles if r["name"] == "manager"]
    resp = client.post(
        f"/api/v1/rbac/users/{user['id']}/roles",
        headers=headers,
        json={"role_ids": role_ids},
    )
    assert resp.status_code == 200, resp.text

    resp = client.get("/api/v1/audit/logs?action=rbac.role_assign", headers=headers)
    assert resp.status_code == 200, resp.text
    entry = resp.json()["items"][0]
    assert entry["resource_id"] == user["id"]

    drawer = client.post(
        "/api/v1/drawers/open", headers=headers, json={"starting_cash": 10.0}
    ).json()
    resp = client.post(
        f"/api/v1/drawers/reconcile/{drawer['id']}",
        headers=headers,
        json={"expected_cash": 10.0, "counted_cash": 12.0},
    )
    assert resp.status_code == 200, resp.text
    resp = client.get("/api/v1/audit/logs?action=drawer.reconcile", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["total"] >= 1
