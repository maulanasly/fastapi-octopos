"""Integration tests for the orders API: stock, settlement, split payments,
cancel/rollback, and idempotency."""

from datetime import UTC

from conftest import order_payload


def _create_checked_out_order(
    client, headers, product_id, quantity=2, idempotency_key=None
):
    resp = client.post(
        "/api/v1/orders/",
        headers=headers,
        json=order_payload(product_id, quantity, idempotency_key),
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_create_order_deducts_stock(
    client, cashier_headers, make_product, open_drawer, manager_headers
):
    product = make_product(
        manager_headers, name="Stock Item", sku="SKU-STOCK", price=25.0, stock=10
    )
    open_drawer(cashier_headers)

    order = _create_checked_out_order(
        client, cashier_headers, product["id"], quantity=3
    )

    assert order["status"] == "pending"
    assert order["reservation_status"] == "reserved"
    assert order["total_amount"] == 75.0
    assert order["remaining_amount"] == 75.0

    products = client.get("/api/v1/products/", headers=cashier_headers).json()
    updated = next(p for p in products if p["id"] == product["id"])
    assert updated["stock_quantity"] == 7


def test_payment_completes_order_when_fully_paid(
    client, cashier_headers, make_product, open_drawer, manager_headers
):
    product = make_product(manager_headers, name="Full Pay", sku="SKU-FULL", price=50.0)
    open_drawer(cashier_headers)
    order = _create_checked_out_order(
        client, cashier_headers, product["id"], quantity=2
    )

    resp = client.post(
        f"/api/v1/orders/{order['id']}/payments",
        headers=cashier_headers,
        json={"payment_method": "cash", "amount": 100.0},
    )
    assert resp.status_code == 200, resp.text

    detail = client.get(
        f"/api/v1/orders/{order['id']}/receipt", headers=cashier_headers
    )
    assert detail.status_code == 200, detail.text
    receipt = detail.json()
    assert receipt["status"] == "serving"
    assert receipt["paid_amount"] == 100.0
    assert receipt["remaining_amount"] == 0.0


def test_cash_overpayment_records_change(
    client, cashier_headers, make_product, open_drawer, manager_headers
):
    product = make_product(manager_headers, name="Change", sku="SKU-CHG", price=50.0)
    open_drawer(cashier_headers)
    order = _create_checked_out_order(
        client, cashier_headers, product["id"], quantity=1
    )

    resp = client.post(
        f"/api/v1/orders/{order['id']}/payments",
        headers=cashier_headers,
        json={"payment_method": "cash", "amount": 60.0},
    )
    assert resp.status_code == 200, resp.text

    receipt = client.get(
        f"/api/v1/orders/{order['id']}/receipt", headers=cashier_headers
    ).json()
    assert receipt["status"] == "serving"
    assert receipt["change_amount"] == 10.0


def test_non_cash_overpayment_rejected(
    client, cashier_headers, make_product, open_drawer, manager_headers
):
    product = make_product(manager_headers, name="Card Cap", sku="SKU-CAP", price=50.0)
    open_drawer(cashier_headers)
    order = _create_checked_out_order(
        client, cashier_headers, product["id"], quantity=1
    )

    resp = client.post(
        f"/api/v1/orders/{order['id']}/payments",
        headers=cashier_headers,
        json={"payment_method": "card", "amount": 60.0},
    )
    assert resp.status_code == 400


def test_split_payments_settle_order(
    client, cashier_headers, make_product, open_drawer, manager_headers
):
    product = make_product(manager_headers, name="Split", sku="SKU-SPLIT", price=50.0)
    open_drawer(cashier_headers)
    order = _create_checked_out_order(
        client, cashier_headers, product["id"], quantity=2
    )

    resp = client.post(
        f"/api/v1/orders/{order['id']}/payments/split",
        headers=cashier_headers,
        json={
            "payments": [
                {"payment_method": "cash", "amount": 50.0},
                {"payment_method": "card", "amount": 50.0},
            ]
        },
    )
    assert resp.status_code == 200, resp.text

    receipt = client.get(
        f"/api/v1/orders/{order['id']}/receipt", headers=cashier_headers
    ).json()
    assert receipt["status"] == "serving"
    assert receipt["paid_amount"] == 100.0
    assert len(receipt["payments"]) == 2


def test_split_payments_retry_is_idempotent(
    client, cashier_headers, make_product, open_drawer, manager_headers
):
    product = make_product(
        manager_headers, name="Split Retry", sku="SKU-SPLIT-R", price=50.0
    )
    open_drawer(cashier_headers)
    order = _create_checked_out_order(
        client, cashier_headers, product["id"], quantity=2
    )

    payload = {
        "payments": [
            {"payment_method": "cash", "amount": 50.0, "idempotency_key": "split-k-1"},
            {"payment_method": "card", "amount": 50.0, "idempotency_key": "split-k-2"},
        ]
    }
    first = client.post(
        f"/api/v1/orders/{order['id']}/payments/split",
        headers=cashier_headers,
        json=payload,
    )
    assert first.status_code == 200, first.text

    # identical retry must not double-pay
    retry = client.post(
        f"/api/v1/orders/{order['id']}/payments/split",
        headers=cashier_headers,
        json=payload,
    )
    assert retry.status_code == 200, retry.text

    receipt = client.get(
        f"/api/v1/orders/{order['id']}/receipt", headers=cashier_headers
    ).json()
    assert receipt["status"] == "serving"
    assert receipt["paid_amount"] == 100.0
    assert len(receipt["payments"]) == 2


def test_cancel_order_restores_stock(
    client, cashier_headers, make_product, open_drawer, manager_headers
):
    product = make_product(
        manager_headers, name="Cancel Me", sku="SKU-CXL", price=20.0, stock=5
    )
    open_drawer(cashier_headers)
    order = _create_checked_out_order(
        client, cashier_headers, product["id"], quantity=2
    )

    resp = client.post(f"/api/v1/orders/{order['id']}/cancel", headers=cashier_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "cancelled"

    products = client.get("/api/v1/products/", headers=cashier_headers).json()
    updated = next(p for p in products if p["id"] == product["id"])
    assert updated["stock_quantity"] == 5


def test_order_idempotency_replays_same_order(
    client, cashier_headers, make_product, open_drawer, manager_headers
):
    product = make_product(manager_headers, name="Idem", sku="SKU-IDEM", price=10.0)
    open_drawer(cashier_headers)

    first = _create_checked_out_order(
        client, cashier_headers, product["id"], quantity=1, idempotency_key="order-ik-1"
    )
    replay = _create_checked_out_order(
        client, cashier_headers, product["id"], quantity=1, idempotency_key="order-ik-1"
    )
    assert replay["id"] == first["id"]

    orders = client.get("/api/v1/orders/", headers=cashier_headers).json()
    assert len(orders) == 1


def test_payment_idempotency_replays_same_payment(
    client, cashier_headers, make_product, open_drawer, manager_headers
):
    product = make_product(
        manager_headers, name="Pay Idem", sku="SKU-PAYIDEM", price=50.0
    )
    open_drawer(cashier_headers)
    order = _create_checked_out_order(
        client, cashier_headers, product["id"], quantity=2
    )

    first = client.post(
        f"/api/v1/orders/{order['id']}/payments",
        headers=cashier_headers,
        json={"payment_method": "card", "amount": 100.0, "idempotency_key": "pay-ik-1"},
    )
    assert first.status_code == 200, first.text

    replay = client.post(
        f"/api/v1/orders/{order['id']}/payments",
        headers=cashier_headers,
        json={"payment_method": "card", "amount": 100.0, "idempotency_key": "pay-ik-1"},
    )
    assert replay.status_code == 200
    assert replay.json()["id"] == first.json()["id"]


def test_payment_on_cancelled_order_rejected(
    client, cashier_headers, make_product, open_drawer, manager_headers
):
    product = make_product(
        manager_headers, name="CXL Pay", sku="SKU-CXLPAY", price=50.0
    )
    open_drawer(cashier_headers)
    order = _create_checked_out_order(
        client, cashier_headers, product["id"], quantity=1
    )
    client.post(f"/api/v1/orders/{order['id']}/cancel", headers=cashier_headers)

    resp = client.post(
        f"/api/v1/orders/{order['id']}/payments",
        headers=cashier_headers,
        json={"payment_method": "cash", "amount": 50.0},
    )
    assert resp.status_code == 400


def test_order_requires_drawer_session(
    client, cashier_headers, make_product, manager_headers
):
    product = make_product(
        manager_headers, name="No Drawer", sku="SKU-NODRW", price=10.0
    )
    resp = client.post(
        "/api/v1/orders/",
        headers=cashier_headers,
        json=order_payload(product["id"]),
    )
    assert resp.status_code == 400


def test_insufficient_stock_rejected(
    client, cashier_headers, make_product, open_drawer, manager_headers
):
    product = make_product(
        manager_headers, name="Low Stock", sku="SKU-LOW", price=10.0, stock=1
    )
    open_drawer(cashier_headers)
    resp = client.post(
        "/api/v1/orders/",
        headers=cashier_headers,
        json=order_payload(product["id"], quantity=5),
    )
    assert resp.status_code == 400
    assert "Not enough stock" in resp.json()["detail"]


def test_release_expired_reservations_for_user_releases_stock(
    client, cashier_headers, manager_headers, make_product, open_drawer, db
):
    from datetime import datetime, timedelta

    from app.models.order import Order
    from app.models.user import User
    from app.services.orders import release_expired_reservations_for_user

    product = make_product(
        manager_headers, name="Expiring", sku="SKU-EXP", price=10.0, stock=5
    )
    open_drawer(cashier_headers)
    order = _create_checked_out_order(
        client, cashier_headers, product["id"], quantity=2
    )

    db_order = db.get(Order, order["id"])
    db_order.reservation_expires_at = datetime.now(UTC) - timedelta(hours=1)
    db.add(db_order)
    db.commit()

    manager = db.query(User).filter(User.email == "manager@example.com").one()
    summary = release_expired_reservations_for_user(db=db, user_id=manager.id)
    assert summary.released_count == 1
    assert summary.released_order_ids == [order["id"]]

    db.refresh(db_order)
    assert db_order.reservation_status == "released"

    products = client.get("/api/v1/products/", headers=cashier_headers).json()
    updated = next(p for p in products if p["id"] == product["id"])
    assert updated["stock_quantity"] == 5


def test_receipt_includes_customer_name(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    product = make_product(
        manager_headers, name="Guest Item", sku="GUEST-1", price=5.0, stock=10
    )
    customer = client.post(
        "/api/v1/customers/", headers=cashier_headers, json={"name": "Walk-in John"}
    ).json()
    open_drawer(cashier_headers)
    order = client.post(
        "/api/v1/orders/",
        headers=cashier_headers,
        json=order_payload(product["id"], customer_id=customer["id"]),
    )
    assert order.status_code == 200, order.text
    receipt = client.get(
        f"/api/v1/orders/{order.json()['id']}/receipt", headers=cashier_headers
    )
    assert receipt.status_code == 200, receipt.text
    assert receipt.json()["customer_name"] == "Walk-in John"


def test_receipt_customer_name_null_for_guest(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    product = make_product(
        manager_headers, name="Guest Item 2", sku="GUEST-2", price=5.0, stock=10
    )
    open_drawer(cashier_headers)
    order = client.post(
        "/api/v1/orders/", headers=cashier_headers, json=order_payload(product["id"])
    )
    assert order.status_code == 200, order.text
    receipt = client.get(
        f"/api/v1/orders/{order.json()['id']}/receipt", headers=cashier_headers
    )
    assert receipt.status_code == 200, receipt.text
    assert receipt.json()["customer_name"] is None


def test_receipt_includes_cashier_name(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    product = make_product(
        manager_headers, name="Cashier Item", sku="CSHR-1", price=5.0, stock=10
    )
    open_drawer(cashier_headers)
    order = client.post(
        "/api/v1/orders/", headers=cashier_headers, json=order_payload(product["id"])
    )
    assert order.status_code == 200, order.text
    receipt = client.get(
        f"/api/v1/orders/{order.json()['id']}/receipt", headers=cashier_headers
    )
    assert receipt.status_code == 200, receipt.text
    body = receipt.json()
    assert body["cashier_name"] is not None
    # fallback to email when no full name
    assert (
        body["cashier_name"].endswith("example.com") or "@" not in body["cashier_name"]
    )


def test_create_order_snapshots_product_unit_cost(
    client, db, cashier_headers, make_product, open_drawer, manager_headers
):
    """The sold line stores the product's current cost for COGS reporting."""
    from app.models.order import OrderItem

    product = make_product(
        manager_headers,
        name="Costed Item",
        sku="SKU-COSTED",
        price=30.0,
        unit_cost=12.5,
        stock=10,
    )
    open_drawer(cashier_headers)

    order = _create_checked_out_order(
        client, cashier_headers, product["id"], quantity=2
    )

    item = db.get(OrderItem, order["items"][0]["id"])
    assert item is not None
    assert float(item.unit_cost) == 12.5


def test_create_order_unit_cost_stays_null_when_unknown(
    client, db, cashier_headers, make_product, open_drawer, manager_headers
):
    """Products without a cost yet produce NULL snapshots (excluded from
    margin math instead of being counted as free)."""
    from app.models.order import OrderItem

    product = make_product(
        manager_headers, name="Uncosted Item", sku="SKU-UNCOSTED", price=20.0
    )
    open_drawer(cashier_headers)

    order = _create_checked_out_order(
        client, cashier_headers, product["id"], quantity=1
    )

    item = db.get(OrderItem, order["items"][0]["id"])
    assert item is not None
    assert item.unit_cost is None
