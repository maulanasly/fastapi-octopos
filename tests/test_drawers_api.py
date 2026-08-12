"""Integration tests for the drawers API: open, close, and reconcile flows."""

from conftest import order_payload


def _open_drawer(client, headers, starting_cash=100.0):
    resp = client.post(
        "/api/v1/drawers/open",
        headers=headers,
        json={"starting_cash": starting_cash},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _paid_order(client, headers, product, quantity, payment_method, amount):
    order = client.post(
        "/api/v1/orders/",
        headers=headers,
        json=order_payload(product["id"], quantity=quantity),
    )
    assert order.status_code == 200, order.text
    paid = client.post(
        f"/api/v1/orders/{order.json()['id']}/payments",
        headers=headers,
        json={"payment_method": payment_method, "amount": amount},
    )
    assert paid.status_code == 200, paid.text
    return order.json()


def _refund(client, headers, order, order_item_id, quantity, payment_method=None):
    payload = {
        "order_id": order["id"],
        "items": [{"order_item_id": order_item_id, "quantity": quantity}],
    }
    if payment_method:
        payload["payment_method"] = payment_method
    resp = client.post("/api/v1/refunds/", headers=headers, json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _completed_order(client, headers, product, quantity=2):
    order = client.post(
        "/api/v1/orders/",
        headers=headers,
        json=order_payload(product["id"], quantity=quantity),
    )
    assert order.status_code == 200, order.text
    paid = client.post(
        f"/api/v1/orders/{order.json()['id']}/payments",
        headers=headers,
        json={"payment_method": "cash", "amount": product["price"] * quantity},
    )
    assert paid.status_code == 200, paid.text
    return order.json()


def test_drawer_lifecycle_close_records_ending_cash(
    client, cashier_headers, make_product, open_drawer, manager_headers
):
    drawer = open_drawer(cashier_headers)
    assert drawer["status"] == "open"

    close = client.post(
        f"/api/v1/drawers/close/{drawer['id']}",
        headers=cashier_headers,
        json={"ending_cash": 150.0},
    )
    assert close.status_code == 200, close.text
    assert close.json()["status"] == "closed"
    assert close.json()["ending_cash"] == 150.0


def test_second_open_drawer_rejected(client, cashier_headers, open_drawer):
    open_drawer(cashier_headers)
    resp = client.post(
        "/api/v1/drawers/open",
        headers=cashier_headers,
        json={"starting_cash": 50.0},
    )
    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"]


def test_reconcile_computes_variances(
    client, cashier_headers, make_product, open_drawer, manager_headers
):
    product = make_product(
        manager_headers, name="Drawer Item", sku="SKU-DRW", price=50.0
    )
    open_drawer(cashier_headers, starting_cash=100.0)
    _completed_order(client, cashier_headers, product, quantity=2)

    resp = client.post(
        "/api/v1/drawers/reconcile/1",
        headers=cashier_headers,
        json={"counted_cash": 210.0, "notes": "over by 10"},
    )
    assert resp.status_code == 200, resp.text
    rec = resp.json()
    assert rec["cash_sales_total"] == 100.0
    assert rec["expected_cash"] == 200.0
    assert rec["counted_cash"] == 210.0
    assert rec["cash_variance"] == 10.0
    assert rec["completed_order_count"] == 1
    assert rec["gross_sales_total"] == 100.0
    assert rec["net_sales_total"] == 100.0


def test_reconcile_card_refund_does_not_reduce_cash_pool(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    product = make_product(
        manager_headers, name="Card Item", sku="SKU-CARD", price=50.0, stock=10
    )
    open_drawer(cashier_headers, starting_cash=100.0)
    order = _paid_order(
        client, cashier_headers, product, quantity=1, payment_method="card", amount=50.0
    )
    _refund(
        client,
        cashier_headers,
        order,
        order["items"][0]["id"],
        quantity=1,
        payment_method="card",
    )

    resp = client.post(
        "/api/v1/drawers/reconcile/1",
        headers=cashier_headers,
        json={"counted_cash": 100.0},
    )
    assert resp.status_code == 200, resp.text
    rec = resp.json()
    assert rec["cash_sales_total"] == 0.0
    assert rec["non_cash_sales_total"] == 50.0
    assert rec["cash_refunds_total"] == 0.0
    assert rec["non_cash_refunds_total"] == 50.0
    assert rec["refunds_total"] == 50.0
    assert rec["expected_cash"] == 100.0
    assert rec["expected_non_cash"] == 0.0
    assert rec["net_sales_total"] == 0.0


def test_reconcile_cash_refund_reduces_expected_cash(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    product = make_product(
        manager_headers, name="Cash Item", sku="SKU-CSH", price=50.0, stock=10
    )
    open_drawer(cashier_headers, starting_cash=100.0)
    order = _paid_order(
        client, cashier_headers, product, quantity=1, payment_method="cash", amount=50.0
    )
    _refund(
        client,
        cashier_headers,
        order,
        order["items"][0]["id"],
        quantity=1,
        payment_method="cash",
    )

    resp = client.post(
        "/api/v1/drawers/reconcile/1",
        headers=cashier_headers,
        json={"counted_cash": 100.0},
    )
    assert resp.status_code == 200, resp.text
    rec = resp.json()
    assert rec["cash_refunds_total"] == 50.0
    assert rec["non_cash_refunds_total"] == 0.0
    assert rec["expected_cash"] == 100.0
    assert rec["expected_non_cash"] == 0.0


def test_reconcile_mixed_payment_methods_split_refunds(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    cash_product = make_product(
        manager_headers, name="Mix Cash", sku="SKU-MXC", price=50.0, stock=10
    )
    card_product = make_product(
        manager_headers, name="Mix Card", sku="SKU-MXD", price=40.0, stock=10
    )
    open_drawer(cashier_headers, starting_cash=100.0)
    cash_order = _paid_order(
        client,
        cashier_headers,
        cash_product,
        quantity=2,
        payment_method="cash",
        amount=100.0,
    )
    card_order = _paid_order(
        client,
        cashier_headers,
        card_product,
        quantity=1,
        payment_method="card",
        amount=40.0,
    )
    _refund(
        client,
        cashier_headers,
        cash_order,
        cash_order["items"][0]["id"],
        quantity=1,
        payment_method="cash",
    )
    _refund(
        client,
        cashier_headers,
        card_order,
        card_order["items"][0]["id"],
        quantity=1,
        payment_method="card",
    )

    resp = client.post(
        "/api/v1/drawers/reconcile/1",
        headers=cashier_headers,
        json={"counted_cash": 150.0},
    )
    assert resp.status_code == 200, resp.text
    rec = resp.json()
    assert rec["cash_sales_total"] == 100.0
    assert rec["non_cash_sales_total"] == 40.0
    assert rec["cash_refunds_total"] == 50.0
    assert rec["non_cash_refunds_total"] == 40.0
    assert rec["refunds_total"] == 90.0
    assert rec["expected_cash"] == 150.0
    assert rec["expected_non_cash"] == 0.0
    assert rec["completed_order_count"] == 2


def test_reconcile_twice_rejected(client, cashier_headers, open_drawer):
    drawer = open_drawer(cashier_headers)
    first = client.post(
        f"/api/v1/drawers/reconcile/{drawer['id']}",
        headers=cashier_headers,
        json={"counted_cash": 100.0},
    )
    assert first.status_code == 200, first.text

    second = client.post(
        f"/api/v1/drawers/reconcile/{drawer['id']}",
        headers=cashier_headers,
        json={"counted_cash": 100.0},
    )
    assert second.status_code == 400


def test_reconcile_another_users_drawer_forbidden(client, auth_factory, open_drawer):
    user_a = auth_factory.user("drawer-a@example.com")
    drawer = open_drawer(user_a)

    user_b = auth_factory.user("drawer-b@example.com")
    resp = client.post(
        f"/api/v1/drawers/reconcile/{drawer['id']}",
        headers=user_b,
        json={"counted_cash": 100.0},
    )
    assert resp.status_code == 403


def test_reconcile_closed_drawer_rejected(client, cashier_headers, open_drawer):
    drawer = open_drawer(cashier_headers)
    client.post(
        f"/api/v1/drawers/close/{drawer['id']}",
        headers=cashier_headers,
        json={"ending_cash": 100.0},
    )
    resp = client.post(
        f"/api/v1/drawers/reconcile/{drawer['id']}",
        headers=cashier_headers,
        json={"counted_cash": 100.0},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Only open drawer sessions can be reconciled."


def test_get_active_drawer_returns_open_session(client, cashier_headers, open_drawer):
    open_drawer(cashier_headers)
    resp = client.get("/api/v1/drawers/active", headers=cashier_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "open"


def test_get_active_drawer_404_when_none(client, cashier_headers):
    resp = client.get("/api/v1/drawers/active", headers=cashier_headers)
    assert resp.status_code == 404
