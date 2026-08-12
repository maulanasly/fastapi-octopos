"""Integration tests for the promotions API: CRUD, validation, order discounts."""

from conftest import order_payload


def _promo_payload(code="SAVE20", discount_value=20.0, **overrides):
    payload = {
        "code": code,
        "name": "Save Twenty",
        "discount_type": "fixed",
        "discount_value": discount_value,
        "applies_to": "order",
    }
    payload.update(overrides)
    return payload


def test_cashier_cannot_create_promotion(client, cashier_headers):
    resp = client.post(
        "/api/v1/promotions/", headers=cashier_headers, json=_promo_payload()
    )
    assert resp.status_code == 403


def test_manager_creates_promotion_with_uppercased_code(client, manager_headers):
    resp = client.post(
        "/api/v1/promotions/", headers=manager_headers, json=_promo_payload("save20")
    )
    assert resp.status_code == 200, resp.text
    promo = resp.json()
    assert promo["code"] == "SAVE20"
    assert promo["is_active"] is True


def test_duplicate_promotion_code_rejected(client, manager_headers):
    client.post("/api/v1/promotions/", headers=manager_headers, json=_promo_payload())
    dup = client.post(
        "/api/v1/promotions/", headers=manager_headers, json=_promo_payload()
    )
    assert dup.status_code == 400
    assert dup.json()["detail"] == "Promotion code already exists"


def test_invalid_discount_type_rejected(client, manager_headers):
    resp = client.post(
        "/api/v1/promotions/",
        headers=manager_headers,
        json=_promo_payload(discount_type="bogo"),
    )
    assert resp.status_code == 400


def test_percentage_over_100_rejected(client, manager_headers):
    resp = client.post(
        "/api/v1/promotions/",
        headers=manager_headers,
        json=_promo_payload(
            code="FREE", discount_type="percentage", discount_value=150
        ),
    )
    assert resp.status_code == 400


def test_product_scope_promotion_requires_existing_product(
    client, manager_headers, make_product
):
    product = make_product(
        manager_headers, name="Promo Product", sku="SKU-PROMO", price=50.0
    )
    resp = client.post(
        "/api/v1/promotions/",
        headers=manager_headers,
        json=_promo_payload(
            code="PPROD", applies_to="product", product_id=product["id"]
        ),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["applies_to"] == "product"


def test_product_scope_with_missing_product_rejected(client, manager_headers):
    resp = client.post(
        "/api/v1/promotions/",
        headers=manager_headers,
        json=_promo_payload(code="GHOST", applies_to="product"),
    )
    assert resp.status_code == 400


def test_fixed_discount_applied_to_order(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    product = make_product(
        manager_headers, name="Disc Item", sku="SKU-DISC", price=100.0
    )
    client.post("/api/v1/promotions/", headers=manager_headers, json=_promo_payload())
    open_drawer(cashier_headers)

    order = client.post(
        "/api/v1/orders/",
        headers=cashier_headers,
        json={**order_payload(product["id"]), "promotion_code": "SAVE20"},
    )
    assert order.status_code == 200, order.text
    body = order.json()
    assert body["discount_amount"] == 20.0
    assert body["total_amount"] == 80.0
    assert body["promotion_id"] is not None


def test_inactive_promotion_code_rejected(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    product = make_product(
        manager_headers, name="Inactive Promo", sku="SKU-IPROMO", price=100.0
    )
    promo = client.post(
        "/api/v1/promotions/", headers=manager_headers, json=_promo_payload("GONE")
    ).json()
    deactivated = client.delete(
        f"/api/v1/promotions/{promo['id']}", headers=manager_headers
    )
    assert deactivated.status_code == 200

    open_drawer(cashier_headers)
    order = client.post(
        "/api/v1/orders/",
        headers=cashier_headers,
        json={**order_payload(product["id"]), "promotion_code": "GONE"},
    )
    assert order.status_code == 400
    assert "inactive" in order.json()["detail"].lower()


def test_update_promotion_discount_value(client, manager_headers):
    promo = client.post(
        "/api/v1/promotions/", headers=manager_headers, json=_promo_payload()
    ).json()
    updated = client.put(
        f"/api/v1/promotions/{promo['id']}",
        headers=manager_headers,
        json={"discount_value": 35.0},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["discount_value"] == 35.0


def test_get_promotion_404(client, manager_headers):
    resp = client.get("/api/v1/promotions/99999", headers=manager_headers)
    assert resp.status_code == 404
