"""Tests for scheduled auto-generation of purchase orders."""

from fastapi.testclient import TestClient

from app.models.user import User
from app.services.auto_po import auto_generate_purchase_orders


def _login(client, email, password="TestPass123"):
    resp = client.post(
        "/api/v1/auth/token",
        data={
            "username": email,
            "password": password,
        },
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _seed(db, client, headers, name, sku, price, stock, reorder_point=100):
    cat = client.post(
        "/api/v1/products/categories", headers=headers, json={"name": f"Cat {sku}"}
    ).json()
    return client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "name": name,
            "sku": sku,
            "price": price,
            "stock_quantity": stock,
            "min_stock": 2,
            "max_stock": 200,
            "reorder_point": reorder_point,
            "lead_time_days": 3,
            "category_id": cat["id"],
        },
    ).json()


def test_auto_po_creates_draft_for_reorder_products(
    client: TestClient, db, manager_headers, auth_factory
):
    owner = auth_factory.register("po-owner@example.com")
    u = db.get(User, owner["id"])
    u.is_superuser = True
    db.commit()

    supplier = client.post(
        "/api/v1/purchasing/suppliers",
        headers=manager_headers,
        json={"name": "Acme Supplies", "is_active": True},
    )
    assert supplier.status_code == 200, supplier.text
    supplier_id = supplier.json()["id"]

    product = _seed(
        db,
        client,
        manager_headers,
        "Low Stock Item",
        "LOW-1",
        10.0,
        5,
        reorder_point=100,
    )

    # give the product supplier history via a prior purchase order (then close it,
    # so it is no longer a pending PO yet still records the supplier link)
    po = client.post(
        "/api/v1/purchasing/orders",
        headers=manager_headers,
        json={
            "supplier_id": supplier_id,
            "items": [
                {"product_id": product["id"], "quantity_ordered": 10, "unit_cost": 10.0}
            ],
        },
    )
    assert po.status_code == 200, po.text
    cancelled = client.post(
        f"/api/v1/purchasing/orders/{po.json()['id']}/cancel", headers=manager_headers
    )
    assert cancelled.status_code == 200, cancelled.text

    result = auto_generate_purchase_orders(db=db, lookback_days=30)
    db.commit()
    assert result["generated"] == 1, result
    po_id = result["po_ids"][0]

    # the new PO is a draft attributed to the superuser
    owner_h = _login(client, "po-owner@example.com")
    resp = client.get(f"/api/v1/purchasing/orders/{po_id}", headers=owner_h)
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "draft"

    # idempotent: second run skips because a pending PO exists
    result2 = auto_generate_purchase_orders(db=db, lookback_days=30)
    db.commit()
    assert result2["generated"] == 0, result2


def test_auto_po_skips_products_without_supplier_history(
    client: TestClient, db, manager_headers, auth_factory
):
    owner = auth_factory.register("po-owner2@example.com")
    u = db.get(User, owner["id"])
    u.is_superuser = True
    db.commit()

    product = _seed(
        db, client, manager_headers, "No Supplier", "NOSUP-1", 5.0, 3, reorder_point=50
    )

    result = auto_generate_purchase_orders(db=db, lookback_days=30)
    db.commit()
    assert result["generated"] == 0, result
    assert any(
        skip["product_id"] == product["id"] and "supplier" in skip["reason"]
        for skip in result["skipped_products"]
    ), result
