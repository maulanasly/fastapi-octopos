"""Integration tests for the inventory API: movements and replenishment."""

from conftest import order_payload


def _sell(client, headers, product, quantity=2):
    order = client.post(
        "/api/v1/orders/",
        headers=headers,
        json=order_payload(product["id"], quantity=quantity),
    )
    assert order.status_code == 200, order.text
    return order.json()


def test_sale_movement_recorded(
    client, cashier_headers, make_product, open_drawer, manager_headers
):
    product = make_product(
        manager_headers, name="Move Item", sku="SKU-MOVE", price=10.0, stock=5
    )
    open_drawer(cashier_headers)
    _sell(client, cashier_headers, product, quantity=2)

    movements = client.get("/api/v1/inventory/movements", headers=cashier_headers)
    assert movements.status_code == 200, movements.text
    rows = [m for m in movements.json() if m["movement_type"] == "sale"]
    assert len(rows) == 1
    assert rows[0]["product_id"] == product["id"]
    assert rows[0]["quantity_delta"] == -2
    assert rows[0]["quantity_before"] == 5
    assert rows[0]["quantity_after"] == 3


def test_movements_filtered_by_product(
    client, cashier_headers, make_product, open_drawer, manager_headers
):
    p1 = make_product(manager_headers, name="Filter A", sku="SKU-FA", price=10.0)
    p2 = make_product(manager_headers, name="Filter B", sku="SKU-FB", price=10.0)
    open_drawer(cashier_headers)
    _sell(client, cashier_headers, p1)
    _sell(client, cashier_headers, p2)

    rows = client.get(
        f"/api/v1/inventory/movements?product_id={p1['id']}",
        headers=cashier_headers,
    ).json()
    rows = [m for m in rows if m["movement_type"] == "sale"]
    assert len(rows) == 1
    assert rows[0]["product_id"] == p1["id"]


def test_refund_movement_recorded(
    client, cashier_headers, make_product, open_drawer, manager_headers
):
    product = make_product(manager_headers, name="Ref Move", sku="SKU-RM", price=10.0)
    open_drawer(cashier_headers)
    order = _sell(client, cashier_headers, product, quantity=2)
    client.post(
        f"/api/v1/orders/{order['id']}/payments",
        headers=cashier_headers,
        json={"payment_method": "cash", "amount": 20.0},
    )
    refund = client.post(
        "/api/v1/refunds/",
        headers=cashier_headers,
        json={
            "order_id": order["id"],
            "items": [{"order_item_id": order["items"][0]["id"], "quantity": 1}],
        },
    )
    assert refund.status_code == 200, refund.text

    rows = client.get("/api/v1/inventory/movements", headers=cashier_headers).json()
    types = {row["movement_type"] for row in rows}
    assert {"sale", "refund"} <= types
    refund_row = next(r for r in rows if r["movement_type"] == "refund")
    assert refund_row["quantity_delta"] == 1


def test_replenishment_suggestion_below_reorder_point(
    client, cashier_headers, make_product, manager_headers
):
    make_product(
        manager_headers,
        name="Low Replenish",
        sku="SKU-LR",
        stock=3,
        min_stock=10,
        reorder_point=5,
    )
    make_product(manager_headers, name="Healthy", sku="SKU-HLTH", stock=50)

    suggestions = client.get(
        "/api/v1/inventory/replenishment-suggestions",
        headers=cashier_headers,
    )
    assert suggestions.status_code == 200, suggestions.text
    rows = suggestions.json()
    assert len(rows) == 1
    assert rows[0]["sku"] == "SKU-LR"
    assert rows[0]["should_reorder"] is True
    assert rows[0]["current_stock"] == 3
    assert rows[0]["recommended_order_quantity"] == 7


def test_replenishment_triggers_when_below_min_stock(
    client, cashier_headers, make_product, manager_headers
):
    make_product(
        manager_headers,
        name="Above Reorder Below Min",
        sku="SKU-ARBM",
        stock=7,
        min_stock=10,
        reorder_point=5,
    )

    rows = client.get(
        "/api/v1/inventory/replenishment-suggestions",
        headers=cashier_headers,
    ).json()
    assert len(rows) == 1
    assert rows[0]["sku"] == "SKU-ARBM"
    assert rows[0]["should_reorder"] is True
    assert rows[0]["recommended_order_quantity"] == 3


def test_replenishment_caps_target_at_max_stock(
    client, cashier_headers, make_product, manager_headers
):
    make_product(
        manager_headers,
        name="Capped High",
        sku="SKU-CAPH",
        stock=3,
        min_stock=10,
        max_stock=50,
        reorder_point=5,
    )

    rows = client.get(
        "/api/v1/inventory/replenishment-suggestions",
        headers=cashier_headers,
    ).json()
    assert len(rows) == 1
    assert rows[0]["sku"] == "SKU-CAPH"
    assert rows[0]["should_reorder"] is True
    assert rows[0]["recommended_order_quantity"] == 7


def test_replenishment_caps_target_below_min_stock_target(
    client, cashier_headers, make_product, manager_headers
):
    make_product(
        manager_headers,
        name="Capped Low",
        sku="SKU-CAPL",
        stock=3,
        min_stock=10,
        max_stock=8,
        reorder_point=5,
    )

    rows = client.get(
        "/api/v1/inventory/replenishment-suggestions",
        headers=cashier_headers,
    ).json()
    assert len(rows) == 1
    assert rows[0]["sku"] == "SKU-CAPL"
    assert rows[0]["should_reorder"] is True
    assert rows[0]["recommended_order_quantity"] == 5


def test_replenishment_honors_product_filter(
    client, cashier_headers, make_product, manager_headers
):
    p1 = make_product(
        manager_headers, name="Low A", sku="SKU-LA", stock=1, reorder_point=5
    )
    p2 = make_product(
        manager_headers, name="Low B", sku="SKU-LB", stock=1, reorder_point=5
    )

    rows = client.get(
        f"/api/v1/inventory/replenishment-suggestions?product_id={p1['id']}",
        headers=cashier_headers,
    ).json()
    assert [r["product_id"] for r in rows] == [p1["id"]]
    assert p2["id"] not in [r["product_id"] for r in rows]


def test_replenishment_only_reorder_flag(
    client, cashier_headers, make_product, manager_headers
):
    make_product(manager_headers, name="OK Stock", sku="SKU-OK", stock=100)
    rows = client.get(
        "/api/v1/inventory/replenishment-suggestions?only_reorder_needed=false",
        headers=cashier_headers,
    ).json()
    assert any(r["should_reorder"] is False for r in rows)
