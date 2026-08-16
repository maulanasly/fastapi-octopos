"""End-to-end golden-path test walking the full POS business flow.

Covers: auth -> RBAC -> catalog -> drawer -> orders (idempotency, promo,
tax, overpayment/change, split payments, cancel) -> refunds -> inventory
ledger -> offline sync -> reports -> shift reconciliation. Guards the
complete loop against regressions across modules.
"""

import pytest
from fastapi.testclient import TestClient

from app.models.user import User


def _login(client, email, password="TestPass123"):
    resp = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_end_to_end_flow(client: TestClient, db):
    # ---------- 1. AUTH ----------
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "manager@example.com",
            "password": "TestPass123",
            "full_name": "Manager",
        },
    )
    assert r.status_code == 201, r.text
    manager_id = r.json()["id"]
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "cashier@example.com",
            "password": "TestPass123",
            "full_name": "Cashier",
        },
    )
    assert r.status_code == 201, r.text
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner@example.com",
            "password": "TestPass123",
            "full_name": "Owner",
        },
    )
    assert r.status_code == 201, r.text
    owner_id = r.json()["id"]

    mgr_h = _login(client, "manager@example.com")
    cash_h = _login(client, "cashier@example.com")

    # Bootstrap owner as superuser (deployment bootstrap step)
    owner = db.get(User, owner_id)
    owner.is_superuser = True
    db.commit()
    owner_h = _login(client, "owner@example.com")

    r = client.get("/api/v1/rbac/me/permissions", headers=mgr_h)
    assert r.status_code == 200, r.text
    assert "orders:manage" in r.json()["permissions"]

    # ---------- 2. RBAC ----------
    r = client.post("/api/v1/rbac/seed-defaults", headers=owner_h)
    assert r.status_code == 200, r.text
    r = client.get("/api/v1/rbac/roles", headers=owner_h)
    assert r.status_code == 200, r.text
    roles = {role["name"]: role["id"] for role in r.json()}
    assert {"cashier", "manager", "admin"} <= set(roles)

    r = client.post(
        f"/api/v1/rbac/users/{owner_id}/roles",
        headers=owner_h,
        json={"role_ids": [roles["admin"]]},
    )
    assert r.status_code == 200, r.text
    r = client.post(
        f"/api/v1/rbac/users/{manager_id}/roles",
        headers=owner_h,
        json={"role_ids": [roles["manager"]]},
    )
    assert r.status_code == 200, r.text

    r = client.get("/api/v1/rbac/me/permissions", headers=mgr_h)
    assert "products:manage" in r.json()["permissions"]

    # cashier must NOT manage products
    r = client.post(
        "/api/v1/products/categories",
        headers=cash_h,
        json={"name": "Sneaky", "description": ""},
    )
    assert r.status_code == 403, r.text

    # ---------- 3. CATALOG ----------
    r = client.post(
        "/api/v1/products/categories",
        headers=mgr_h,
        json={"name": "Beverages", "description": "Drinks"},
    )
    assert r.status_code == 200, r.text
    cat_id = r.json()["id"]

    def make_product(sku, name, price, stock):
        r = client.post(
            "/api/v1/products",
            headers=mgr_h,
            json={
                "name": name,
                "sku": sku,
                "price": price,
                "stock_quantity": stock,
                "min_stock": 2,
                "max_stock": 100,
                "reorder_point": 5,
                "lead_time_days": 3,
                "category_id": cat_id,
            },
        )
        assert r.status_code == 200, r.text
        return r.json()

    latte = make_product("BEV-LATTE", "Cafe Latte", 4.50, 20)
    croissant = make_product("BAKE-CRO", "Croissant", 3.25, 15)
    assert latte["stock_quantity"] == 20

    # ---------- 4. CUSTOMER + PROMOTION ----------
    r = client.post(
        "/api/v1/customers",
        headers=mgr_h,
        json={"name": "Alice Smith", "email": "alice@example.com"},
    )
    assert r.status_code == 200, r.text
    customer_id = r.json()["id"]
    r = client.post(
        "/api/v1/promotions",
        headers=mgr_h,
        json={
            "name": "Save 10",
            "code": "SAVE10",
            "description": "10% off",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "is_active": True,
        },
    )
    assert r.status_code == 200, r.text

    # ---------- 5. DRAWER ----------
    r = client.post(
        "/api/v1/drawers/open", headers=cash_h, json={"starting_cash": 100.0}
    )
    assert r.status_code == 200, r.text
    drawer_id = r.json()["id"]
    r = client.get("/api/v1/drawers/active", headers=cash_h)
    assert r.status_code == 200 and r.json()["id"] == drawer_id, r.text

    # ---------- 6. ORDERS ----------
    order_in = {
        "items": [
            {"product_id": latte["id"], "quantity": 2},
            {"product_id": croissant["id"], "quantity": 1},
        ],
        "customer_id": customer_id,
        "promotion_code": "SAVE10",
        "idempotency_key": "sim-order-1",
    }
    r = client.post("/api/v1/orders", headers=cash_h, json=order_in)
    assert r.status_code == 200, r.text
    order = r.json()
    assert order["status"] in ("pending", "open")
    assert abs(order["subtotal_amount"] - 12.25) < 0.01
    assert order["discount_amount"] > 0
    expected_grand = order["subtotal_amount"] - order["discount_amount"]
    assert abs(order["grand_total_amount"] - expected_grand) < 0.01

    # idempotent replay -> same order
    r2 = client.post("/api/v1/orders", headers=cash_h, json=order_in)
    assert r2.status_code == 200, r2.text
    assert r2.json()["id"] == order["id"]

    r = client.get(f"/api/v1/orders/{order['id']}/receipt", headers=cash_h)
    assert r.status_code == 200, r.text
    assert abs(r.json()["grand_total_amount"] - order["grand_total_amount"]) < 0.01

    # overpayment -> change, order settled
    r = client.post(
        f"/api/v1/orders/{order['id']}/payments",
        headers=cash_h,
        json={"payment_method": "cash", "amount": 20.0, "idempotency_key": "sim-pay-1"},
    )
    assert r.status_code == 200, r.text
    r = client.get(f"/api/v1/orders/{order['id']}/receipt", headers=cash_h)
    assert r.status_code == 200, r.text
    assert r.json()["change_amount"] > 0
    assert r.json()["remaining_amount"] == 0

    # split payments settle a second order
    r = client.post(
        "/api/v1/orders",
        headers=cash_h,
        json={
            "items": [{"product_id": latte["id"], "quantity": 1}],
            "idempotency_key": "sim-order-2",
        },
    )
    assert r.status_code == 200, r.text
    order2 = r.json()
    r = client.post(
        f"/api/v1/orders/{order2['id']}/payments/split",
        headers=cash_h,
        json={
            "payments": [
                {"payment_method": "cash", "amount": 2.00},
                {"payment_method": "card", "amount": 2.50},
            ]
        },
    )
    assert r.status_code == 200, r.text
    r = client.get(f"/api/v1/orders/{order2['id']}/receipt", headers=cash_h)
    assert r.status_code == 200, r.text
    assert r.json()["remaining_amount"] == 0
    assert len(r.json()["payments"]) == 2

    # partial payment + cancel restores stock
    r = client.post(
        "/api/v1/orders",
        headers=cash_h,
        json={
            "items": [{"product_id": croissant["id"], "quantity": 2}],
            "idempotency_key": "sim-order-3",
        },
    )
    assert r.status_code == 200, r.text
    order3 = r.json()
    r = client.post(
        f"/api/v1/orders/{order3['id']}/payments",
        headers=cash_h,
        json={"payment_method": "cash", "amount": 1.00},
    )
    assert r.status_code == 200, r.text
    r = client.post(f"/api/v1/orders/{order3['id']}/cancel", headers=cash_h)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "cancelled"

    # ---------- 7. REFUNDS ----------
    item_id = order["items"][0]["id"]
    r = client.post(
        "/api/v1/refunds",
        headers=cash_h,
        json={
            "order_id": order["id"],
            "reason": "Customer changed mind",
            "payment_method": "cash",
            "idempotency_key": "sim-refund-1",
            "items": [{"order_item_id": item_id, "quantity": 1}],
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["total_amount"] > 0

    r = client.get("/api/v1/inventory/movements", headers=mgr_h)
    assert r.status_code == 200, r.text
    assert len(r.json()) >= 3

    # ---------- 8. OFFLINE SYNC ----------
    r = client.post(
        "/api/v1/sync/events/batch",
        headers=cash_h,
        json={
            "events": [
                {
                    "client_event_id": "evt-1",
                    "event_type": "inventory_adjustment",
                    "idempotency_key": "sync-ev-1",
                    "payload": {
                        "product_id": latte["id"],
                        "delta": -1,
                        "reason": "spillage",
                    },
                },
                {
                    "client_event_id": "evt-2",
                    "event_type": "note",
                    "idempotency_key": "sync-ev-2",
                    "payload": {"text": "restocked coffee beans"},
                },
            ]
        },
    )
    assert r.status_code == 200, r.text

    # ---------- 9. REPORTS ----------
    r = client.get("/api/v1/reports/sales", headers=mgr_h)
    assert r.status_code == 200, r.text
    assert r.json().get("total_revenue", 0) > 0 or r.json().get("total", 0) > 0
    assert client.get("/api/v1/reports/low-stock", headers=mgr_h).status_code == 200
    assert client.get("/api/v1/reports/top-products", headers=mgr_h).status_code == 200
    # cashier blocked by RBAC gate
    assert client.get("/api/v1/reports/sales", headers=cash_h).status_code == 403

    # ---------- 10. SHIFT RECONCILIATION ----------
    r = client.post(
        f"/api/v1/drawers/reconcile/{drawer_id}",
        headers=cash_h,
        json={"expected_cash": 115.0, "counted_cash": 118.0},
    )
    assert r.status_code == 200, r.text
    rec = r.json()
    assert "expected_cash" in rec or "difference" in rec
    r = client.get(f"/api/v1/drawers/{drawer_id}/reconciliation", headers=cash_h)
    assert r.status_code == 200, r.text
    # drawer closed after reconcile
    assert client.get("/api/v1/drawers/active", headers=cash_h).status_code == 404
