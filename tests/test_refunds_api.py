"""Integration tests for the refunds API: stock restore, idempotency, and
over-refund guard."""

from conftest import order_payload


def _completed_order(
    client, manager_headers, make_product, open_drawer, name="Refundable", sku="SKU-REF"
):
    product = make_product(manager_headers, name=name, sku=sku, price=50.0, stock=10)
    # Manager owns the order so refunds:create is satisfied regardless of role profile
    open_drawer(manager_headers)
    order = client.post(
        "/api/v1/orders/",
        headers=manager_headers,
        json=order_payload(product["id"], quantity=2),
    )
    assert order.status_code == 200, order.text
    paid = client.post(
        f"/api/v1/orders/{order.json()['id']}/payments",
        headers=manager_headers,
        json={"payment_method": "cash", "amount": 100.0},
    )
    assert paid.status_code == 200, paid.text
    return product, order.json()


def _refund(
    client, manager_headers, order, order_item_id, quantity, idempotency_key=None
):
    payload = {
        "order_id": order["id"],
        "items": [{"order_item_id": order_item_id, "quantity": quantity}],
    }
    if idempotency_key:
        payload["idempotency_key"] = idempotency_key
    return client.post("/api/v1/refunds/", headers=manager_headers, json=payload)


def test_refund_restores_stock(client, manager_headers, make_product, open_drawer):
    product, order = _completed_order(
        client, manager_headers, make_product, open_drawer
    )
    order_item_id = order["items"][0]["id"]

    resp = _refund(client, manager_headers, order, order_item_id, quantity=2)
    assert resp.status_code == 200, resp.text
    refund = resp.json()
    assert refund["total_amount"] == 100.0
    assert refund["order_id"] == order["id"]

    products = client.get("/api/v1/products/", headers=manager_headers).json()
    updated = next(p for p in products if p["id"] == product["id"])
    assert updated["stock_quantity"] == 10


def test_refund_idempotency_returns_same_refund(
    client, manager_headers, make_product, open_drawer
):
    _, order = _completed_order(client, manager_headers, make_product, open_drawer)
    order_item_id = order["items"][0]["id"]

    first = _refund(
        client,
        manager_headers,
        order,
        order_item_id,
        quantity=1,
        idempotency_key="refund-ik-1",
    )
    assert first.status_code == 200, first.text

    replay = _refund(
        client,
        manager_headers,
        order,
        order_item_id,
        quantity=1,
        idempotency_key="refund-ik-1",
    )
    assert replay.status_code == 200
    assert replay.json()["id"] == first.json()["id"]


def test_refund_over_ordered_quantity_rejected(
    client, manager_headers, make_product, open_drawer
):
    _, order = _completed_order(client, manager_headers, make_product, open_drawer)
    order_item_id = order["items"][0]["id"]

    resp = _refund(client, manager_headers, order, order_item_id, quantity=3)
    assert resp.status_code == 400
    assert "exceeds refundable quantity" in resp.json()["detail"]


def test_second_refund_beyond_refundable_rejected(
    client, manager_headers, make_product, open_drawer
):
    _, order = _completed_order(client, manager_headers, make_product, open_drawer)
    order_item_id = order["items"][0]["id"]
    first = _refund(client, manager_headers, order, order_item_id, quantity=2)
    assert first.status_code == 200

    resp = _refund(client, manager_headers, order, order_item_id, quantity=1)
    assert resp.status_code == 400


def test_refund_of_pending_order_rejected(
    client, manager_headers, make_product, open_drawer
):
    product = make_product(
        manager_headers, name="Pending Ref", sku="SKU-PREF", price=50.0
    )
    open_drawer(manager_headers)
    order = client.post(
        "/api/v1/orders/",
        headers=manager_headers,
        json=order_payload(product["id"], quantity=1),
    )
    assert order.status_code == 200, order.text

    resp = _refund(
        client,
        manager_headers,
        order.json(),
        order.json()["items"][0]["id"],
        quantity=1,
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Only completed orders can be refunded"


def test_unknown_order_item_rejected(
    client, manager_headers, make_product, open_drawer
):
    _, order = _completed_order(client, manager_headers, make_product, open_drawer)
    resp = _refund(client, manager_headers, order, order_item_id=99999, quantity=1)
    assert resp.status_code == 400
    assert "not found in order" in resp.json()["detail"]


def _customer_order_flow(
    client, manager_headers, make_product, open_drawer, customer, quantity=2
):
    product = make_product(
        manager_headers, name="Pts Item", sku="SKU-PTS", price=50.0, stock=10
    )
    open_drawer(manager_headers)
    order = client.post(
        "/api/v1/orders/",
        headers=manager_headers,
        json={
            **order_payload(product["id"], quantity=quantity),
            "customer_id": customer["id"],
        },
    )
    assert order.status_code == 200, order.text
    order = order.json()
    paid = client.post(
        f"/api/v1/orders/{order['id']}/payments",
        headers=manager_headers,
        json={"payment_method": "cash", "amount": 100.0},
    )
    assert paid.status_code == 200, paid.text
    return product, order


def test_refund_reverses_earned_points_pro_rata(
    client, manager_headers, make_product, open_drawer
):
    customer = client.post(
        "/api/v1/customers/",
        headers=manager_headers,
        json={"name": "Points Jane", "email": "points-jane@example.com"},
    ).json()
    _, order = _customer_order_flow(
        client, manager_headers, make_product, open_drawer, customer
    )

    after_completion = client.get(
        f"/api/v1/customers/{customer['id']}", headers=manager_headers
    ).json()
    assert after_completion["points_balance"] == 100

    resp = _refund(client, manager_headers, order, order["items"][0]["id"], quantity=1)
    assert resp.status_code == 200, resp.text
    assert resp.json()["total_amount"] == 50.0

    after_refund = client.get(
        f"/api/v1/customers/{customer['id']}", headers=manager_headers
    ).json()
    assert after_refund["points_balance"] == 50

    txns = client.get(
        f"/api/v1/customers/{customer['id']}/loyalty-transactions",
        headers=manager_headers,
    ).json()
    adjust = [t for t in txns if t["transaction_type"] == "adjust"]
    assert len(adjust) == 1
    assert adjust[0]["points_delta"] == -50
    assert adjust[0]["order_id"] == order["id"]


def test_refund_points_reversal_never_goes_negative(
    client, manager_headers, make_product, open_drawer
):
    customer = client.post(
        "/api/v1/customers/",
        headers=manager_headers,
        json={"name": "Points Ken", "email": "points-ken@example.com"},
    ).json()
    _, order = _customer_order_flow(
        client, manager_headers, make_product, open_drawer, customer
    )

    balance = client.get(
        f"/api/v1/customers/{customer['id']}", headers=manager_headers
    ).json()["points_balance"]
    assert balance == 100

    first = _refund(client, manager_headers, order, order["items"][0]["id"], quantity=1)
    assert first.status_code == 200, first.text
    second = _refund(
        client, manager_headers, order, order["items"][0]["id"], quantity=1
    )
    assert second.status_code == 200, second.text

    after = client.get(
        f"/api/v1/customers/{customer['id']}", headers=manager_headers
    ).json()
    assert after["points_balance"] == 0
