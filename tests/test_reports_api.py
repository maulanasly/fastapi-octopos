"""Integration tests for the reports API."""

from conftest import order_payload


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


def _report_setup(client, cashier_headers, manager_headers, make_product, open_drawer):
    product = make_product(
        manager_headers, name="Report Item", sku="SKU-RPT", price=50.0
    )
    open_drawer(cashier_headers)
    order = _completed_order(client, cashier_headers, product, quantity=2)
    return product, order


def test_sales_summary_counts_completed_orders(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    _, _ = _report_setup(
        client, cashier_headers, manager_headers, make_product, open_drawer
    )

    resp = client.get("/api/v1/reports/sales", headers=manager_headers)
    assert resp.status_code == 200, resp.text
    summary = resp.json()
    assert summary["gross_revenue"] == 100.0
    assert summary["total_revenue"] == 100.0
    assert summary["order_count"] == 1
    assert summary["average_order_value"] == 100.0
    assert summary["total_refunds"] == 0.0
    assert summary["net_revenue"] == 100.0


def test_sales_summary_net_of_refunds(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    _, order = _report_setup(
        client, cashier_headers, manager_headers, make_product, open_drawer
    )
    client.post(
        "/api/v1/refunds/",
        headers=cashier_headers,
        json={
            "order_id": order["id"],
            "items": [{"order_item_id": order["items"][0]["id"], "quantity": 1}],
        },
    )

    summary = client.get("/api/v1/reports/sales", headers=manager_headers).json()
    assert summary["total_refunds"] == 50.0
    assert summary["net_revenue"] == 50.0


def test_sales_summary_ignores_pending_orders(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    product = make_product(
        manager_headers, name="Pending Rpt", sku="SKU-PRPT", price=50.0
    )
    open_drawer(cashier_headers)
    client.post(
        "/api/v1/orders/",
        headers=cashier_headers,
        json=order_payload(product["id"]),
    )

    summary = client.get("/api/v1/reports/sales", headers=manager_headers).json()
    assert summary["order_count"] == 0


def test_top_products_ranks_by_quantity(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    p1, _ = _report_setup(
        client, cashier_headers, manager_headers, make_product, open_drawer
    )
    p2 = make_product(manager_headers, name="Report Two", sku="SKU-RPT2", price=10.0)
    _completed_order(client, cashier_headers, p2, quantity=1)

    rows = client.get("/api/v1/reports/top-products", headers=manager_headers).json()
    assert len(rows) == 2
    assert rows[0]["product_id"] == p1["id"]
    assert rows[0]["total_quantity_sold"] == 2
    assert rows[0]["total_revenue"] == 100.0


def test_low_stock_respects_threshold(
    client, cashier_headers, manager_headers, make_product
):
    make_product(manager_headers, name="Low Stock R", sku="SKU-LSR", stock=3)

    below = client.get("/api/v1/reports/low-stock", headers=manager_headers).json()
    assert any(p["stock_quantity"] == 3 for p in below)

    strict = client.get(
        "/api/v1/reports/low-stock?threshold=0", headers=manager_headers
    ).json()
    assert strict == []


def test_top_customers_aggregates_spend(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    customer = client.post(
        "/api/v1/customers/",
        headers=manager_headers,
        json={"name": "Top Buyer", "email": "top@example.com"},
    ).json()
    product = make_product(
        manager_headers, name="Buyer Item", sku="SKU-TOP", price=50.0
    )
    open_drawer(cashier_headers)
    order = client.post(
        "/api/v1/orders/",
        headers=cashier_headers,
        json={
            **order_payload(product["id"], quantity=2),
            "customer_id": customer["id"],
        },
    )
    assert order.status_code == 200, order.text
    client.post(
        f"/api/v1/orders/{order.json()['id']}/payments",
        headers=cashier_headers,
        json={"payment_method": "cash", "amount": 100.0},
    )

    rows = client.get("/api/v1/reports/top-customers", headers=manager_headers).json()
    assert len(rows) == 1
    assert rows[0]["customer_id"] == customer["id"]
    assert rows[0]["order_count"] == 1
    assert rows[0]["total_spent"] == 100.0


def test_tax_liability_empty_when_no_tax_rules(
    client, cashier_headers, manager_headers, make_product, open_drawer, db
):
    # Remove the migration-seeded default rule to test a rule-free install
    from app.models.tax import TaxRule

    for rule in db.query(TaxRule).all():
        db.delete(rule)
    db.commit()

    _, _ = _report_setup(
        client, cashier_headers, manager_headers, make_product, open_drawer
    )
    resp = client.get("/api/v1/reports/tax-liability", headers=manager_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total_tax_amount"] == 0.0
    assert body["items"] == []


def test_reports_require_reports_permission(client, cashier_headers):
    resp = client.get("/api/v1/reports/sales", headers=cashier_headers)
    assert resp.status_code == 403
