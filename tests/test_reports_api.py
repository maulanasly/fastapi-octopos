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


def _purchasing_setup(client, manager_headers, admin_headers, make_product, name, sku):
    product = make_product(manager_headers, name=name, sku=sku, price=15.0)
    supplier_resp = client.post(
        "/api/v1/purchasing/suppliers",
        headers=manager_headers,
        json={"name": name},
    )
    assert supplier_resp.status_code == 200, supplier_resp.text
    supplier = supplier_resp.json()
    po_resp = client.post(
        "/api/v1/purchasing/orders",
        headers=manager_headers,
        json={
            "supplier_id": supplier["id"],
            "items": [
                {
                    "product_id": product["id"],
                    "quantity_ordered": 10,
                    "unit_cost": 4.0,
                }
            ],
        },
    )
    assert po_resp.status_code == 200, po_resp.text
    po = po_resp.json()
    client.post(
        f"/api/v1/purchasing/orders/{po['id']}/submit-review",
        headers=manager_headers,
        json={},
    )
    client.post(
        f"/api/v1/purchasing/orders/{po['id']}/mark-ordered", headers=admin_headers
    )
    client.post(
        f"/api/v1/purchasing/orders/{po['id']}/receive",
        headers=manager_headers,
        json={
            "items": [
                {
                    "purchase_order_item_id": po["items"][0]["id"],
                    "quantity_received": 10,
                }
            ]
        },
    )
    invoice_resp = client.post(
        "/api/v1/purchasing/invoices",
        headers=manager_headers,
        json={
            "purchase_order_id": po["id"],
            "invoice_number": f"INV-{sku}",
            "items": [
                {
                    "purchase_order_item_id": po["items"][0]["id"],
                    "billed_quantity": 10,
                    "billed_unit_cost": 4.5,
                }
            ],
        },
    )
    assert invoice_resp.status_code == 200, invoice_resp.text
    invoice = invoice_resp.json()
    client.post(
        f"/api/v1/purchasing/invoices/{invoice['id']}/submit-review",
        headers=manager_headers,
        json={},
    )
    client.post(
        f"/api/v1/purchasing/invoices/{invoice['id']}/approve",
        headers=admin_headers,
        json={},
    )
    return supplier


def test_supplier_spend_report_ranks_and_estimates_cogs(
    client, manager_headers, admin_headers, make_product
):
    supplier_a = _purchasing_setup(
        client,
        manager_headers,
        admin_headers,
        make_product,
        name="Spend Supplier A",
        sku="SKU-SPA",
    )
    _purchasing_setup(
        client,
        manager_headers,
        admin_headers,
        make_product,
        name="Spend Supplier B",
        sku="SKU-SPB",
    )

    resp = client.get("/api/v1/reports/supplier-spend", headers=manager_headers)
    assert resp.status_code == 200, resp.text
    summary = resp.json()

    assert summary["cogs_estimate"] == 90.0
    items = {item["supplier_id"]: item for item in summary["items"]}
    assert items[supplier_a["id"]]["supplier_name"] == "Spend Supplier A"
    assert items[supplier_a["id"]]["approved_total"] == 45.0
    assert items[supplier_a["id"]]["variance_total"] == 5.0
    assert items[supplier_a["id"]]["po_count"] == 1
    assert items[supplier_a["id"]]["invoice_count"] == 1
    totals = [item["approved_total"] for item in summary["items"]]
    assert totals == sorted(totals, reverse=True)


def test_purchase_variance_trend_buckets_by_month(
    client, manager_headers, admin_headers, make_product
):
    _purchasing_setup(
        client,
        manager_headers,
        admin_headers,
        make_product,
        name="Trend Supplier",
        sku="SKU-TRD",
    )

    resp = client.get("/api/v1/reports/purchase-variance", headers=manager_headers)
    assert resp.status_code == 200, resp.text
    summary = resp.json()

    assert len(summary["months"]) >= 1
    current = summary["months"][-1]
    assert current["invoice_count"] >= 1
    assert current["approved_total"] == 45.0
    assert current["variance_total"] == 5.0
    periods = [month["period"] for month in summary["months"]]
    assert periods == sorted(periods)


def test_sales_summary_margin_uses_cost_snapshot_net_of_refunds(
    client, manager_headers, make_product, open_drawer
):
    """COGS = Σ(sold qty × snapshot cost) − refunds, over known-cost lines
    only; margin is net_revenue − COGS and coverage flags unknown costs."""
    from test_refunds_api import _refund

    # Costed product (cost 10, price 30) and an uncosted one (price 50).
    costed = make_product(
        manager_headers,
        name="Margin Costed",
        sku="SKU-MGN-C",
        price=30.0,
        unit_cost=10.0,
        stock=20,
    )
    uncosted = make_product(
        manager_headers,
        name="Margin Uncosted",
        sku="SKU-MGN-U",
        price=50.0,
        stock=20,
    )
    open_drawer(manager_headers)

    def _buy_and_pay(product, quantity):
        order = client.post(
            "/api/v1/orders/",
            headers=manager_headers,
            json={"items": [{"product_id": product["id"], "quantity": quantity}]},
        )
        assert order.status_code == 200, order.text
        paid = client.post(
            f"/api/v1/orders/{order.json()['id']}/payments",
            headers=manager_headers,
            json={
                "payment_method": "cash",
                "amount": float(product["price"]) * quantity,
            },
        )
        assert paid.status_code == 200, paid.text
        return order.json()

    order_a = _buy_and_pay(costed, 2)  # revenue 60, gross cogs 20
    _buy_and_pay(uncosted, 1)  # revenue 50, no known cost

    # Refund one unit of the costed line: reverses 10 of COGS.
    resp = _refund(
        client,
        manager_headers,
        order_a,
        order_a["items"][0]["id"],
        quantity=1,
    )
    assert resp.status_code == 200, resp.text

    summary = client.get("/api/v1/reports/sales", headers=manager_headers).json()

    assert summary["net_revenue"] == 80.0  # (60 + 50) - 30 refunded
    assert summary["cogs_total"] == 10.0  # 20 sold - 10 refunded
    assert summary["gross_margin_amount"] == 70.0
    assert summary["gross_margin_percent"] == 87.5
    assert summary["cogs_known_ratio"] == round(2 / 3, 4)
