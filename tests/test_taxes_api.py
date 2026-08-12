"""Integration tests for the taxes API: CRUD, validation, order tax calculation."""

from conftest import order_payload


def _rule_payload(name="VAT", rate=10.0, tax_scope="order"):
    return {
        "name": name,
        "tax_scope": tax_scope,
        "tax_mode": "exclusive",
        "rate": rate,
    }


def test_cashier_can_read_rules(client, cashier_headers):
    resp = client.get("/api/v1/taxes/", headers=cashier_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json() == []


def test_cashier_cannot_create_rule(client, cashier_headers):
    resp = client.post("/api/v1/taxes/", headers=cashier_headers, json=_rule_payload())
    assert resp.status_code == 403


def test_manager_creates_and_reads_rule(client, manager_headers):
    created = client.post(
        "/api/v1/taxes/", headers=manager_headers, json=_rule_payload()
    )
    assert created.status_code == 200, created.text
    rule = created.json()
    assert rule["rate"] == 10.0
    assert rule["is_active"] is True

    fetched = client.get(f"/api/v1/taxes/{rule['id']}", headers=manager_headers)
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "VAT"


def test_invalid_tax_scope_rejected(client, manager_headers):
    resp = client.post(
        "/api/v1/taxes/",
        headers=manager_headers,
        json={
            "name": "Bad",
            "tax_scope": "region",
            "tax_mode": "exclusive",
            "rate": 5.0,
        },
    )
    assert resp.status_code == 400


def test_product_scope_rule_applied_to_order(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    product = make_product(
        manager_headers, name="Taxed Item", sku="SKU-TAX", price=100.0
    )
    client.post(
        "/api/v1/taxes/",
        headers=manager_headers,
        json={
            "name": "VAT 10",
            "tax_scope": "product",
            "tax_mode": "exclusive",
            "rate": 10.0,
            "product_id": product["id"],
        },
    )
    open_drawer(cashier_headers)

    order = client.post(
        "/api/v1/orders/",
        headers=cashier_headers,
        json=order_payload(product["id"]),
    )
    assert order.status_code == 200, order.text
    body = order.json()
    assert body["tax_total_amount"] == 10.0
    assert body["grand_total_amount"] == 110.0
    assert len(body["tax_lines"]) == 1
    assert body["tax_lines"][0]["tax_name"] == "VAT 10"


def test_cash_payment_accepted_for_taxed_order(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    product = make_product(
        manager_headers, name="Tax Cash", sku="SKU-TCASH", price=100.0
    )
    client.post(
        "/api/v1/taxes/",
        headers=manager_headers,
        json={
            "name": "VAT",
            "tax_scope": "order",
            "tax_mode": "exclusive",
            "rate": 10.0,
        },
    )
    open_drawer(cashier_headers)
    order = client.post(
        "/api/v1/orders/",
        headers=cashier_headers,
        json=order_payload(product["id"]),
    ).json()

    paid = client.post(
        f"/api/v1/orders/{order['id']}/payments",
        headers=cashier_headers,
        json={"payment_method": "card", "amount": order["grand_total_amount"]},
    )
    assert paid.status_code == 200, paid.text

    receipt = client.get(
        f"/api/v1/orders/{order['id']}/receipt", headers=cashier_headers
    ).json()
    assert receipt["status"] == "completed"
    assert receipt["tax_total_amount"] == 10.0


def test_update_and_deactivate_rule(client, manager_headers):
    rule = client.post(
        "/api/v1/taxes/", headers=manager_headers, json=_rule_payload()
    ).json()

    updated = client.put(
        f"/api/v1/taxes/{rule['id']}",
        headers=manager_headers,
        json={"rate": 12.0},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["rate"] == 12.0

    deactivated = client.delete(f"/api/v1/taxes/{rule['id']}", headers=manager_headers)
    assert deactivated.status_code == 200
    fetched = client.get(f"/api/v1/taxes/{rule['id']}", headers=manager_headers).json()
    assert fetched["is_active"] is False


def test_get_rule_404(client, manager_headers):
    resp = client.get("/api/v1/taxes/99999", headers=manager_headers)
    assert resp.status_code == 404
