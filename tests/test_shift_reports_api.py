"""Tests for shift (Z-)reports and daily-close endpoints."""

from fastapi.testclient import TestClient


def _run_shift(client, db, manager_headers, make_product):
    product = make_product(
        manager_headers, name="Shift Item", sku="SHF-1", price=10.0, stock=10
    )
    drawer = client.post(
        "/api/v1/drawers/open", headers=manager_headers, json={"starting_cash": 50.0}
    )
    assert drawer.status_code == 200, drawer.text
    drawer_id = drawer.json()["id"]

    order = client.post(
        "/api/v1/orders",
        headers=manager_headers,
        json={
            "items": [{"product_id": product["id"], "quantity": 2}],
        },
    )
    assert order.status_code == 200, order.text
    order_id = order.json()["id"]
    pay = client.post(
        f"/api/v1/orders/{order_id}/payments",
        headers=manager_headers,
        json={"payment_method": "cash", "amount": 20.0},
    )
    assert pay.status_code == 200, pay.text

    rec = client.post(
        f"/api/v1/drawers/reconcile/{drawer_id}",
        headers=manager_headers,
        json={"expected_cash": 70.0, "counted_cash": 72.0},
    )
    assert rec.status_code == 200, rec.text
    return rec.json()["id"]


def test_shift_report_totals_match_reconciliation(
    client: TestClient, db, manager_headers, make_product
):
    rec_id = _run_shift(client, db, manager_headers, make_product)

    resp = client.get(f"/api/v1/reports/shift/{rec_id}", headers=manager_headers)
    assert resp.status_code == 200, resp.text
    report = resp.json()
    assert report["reconciliation_id"] == rec_id
    assert report["operator_name"]
    assert report["completed_order_count"] == 1
    assert report["gross_sales_total"] > 0
    assert report["cash_variance"] == 2.0
    assert any(p["payment_method"] == "cash" for p in report["payment_breakdown"])

    resp = client.get("/api/v1/reports/shift/9999", headers=manager_headers)
    assert resp.status_code == 404, resp.text


def test_daily_close_aggregates_shifts(
    client: TestClient, db, manager_headers, make_product
):
    rec_id = _run_shift(client, db, manager_headers, make_product)

    resp = client.get("/api/v1/reports/daily-close", headers=manager_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["totals"]["shift_count"] >= 1
    assert body["totals"]["completed_order_count"] >= 1
    assert body["totals"]["gross_sales_total"] > 0
    ids = [s["reconciliation_id"] for s in body["shifts"]]
    assert rec_id in ids


def test_shift_report_requires_reports_permission(client: TestClient, auth_factory):
    headers = auth_factory.user("shift-no-perm@example.com")
    resp = client.get("/api/v1/reports/shift/1", headers=headers)
    assert resp.status_code == 403, resp.text


def test_shift_list_returns_reconciled_shifts(
    client, db, manager_headers, make_product
):
    rec_id = _run_shift(client, db, manager_headers, make_product)
    resp = client.get("/api/v1/reports/shifts", headers=manager_headers)
    assert resp.status_code == 200, resp.text
    items = resp.json()
    assert any(item["reconciliation_id"] == rec_id for item in items)
    newest = items[0]
    assert newest["operator_name"] is not None
    assert newest["closed_at"] is not None
    assert newest["gross_sales_total"] > 0


def test_shift_list_respects_date_range(client, db, manager_headers, make_product):
    _run_shift(client, db, manager_headers, make_product)
    resp = client.get(
        "/api/v1/reports/shifts",
        headers=manager_headers,
        params={"date_from": "2000-01-01T00:00:00", "date_to": "2000-01-02T00:00:00"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == []


def test_shift_list_requires_reports_permission(client, cashier_headers):
    resp = client.get("/api/v1/reports/shifts", headers=cashier_headers)
    assert resp.status_code == 403, resp.text
