"""Integration tests for the customers API: CRUD, loyalty points, deactivation."""

from conftest import order_payload

CUSTOMER = {"name": "Jane Doe", "email": "jane@example.com", "phone": "555-0100"}


def test_cashier_cannot_create_customer(client, cashier_headers):
    resp = client.post("/api/v1/customers/", headers=cashier_headers, json=CUSTOMER)
    assert resp.status_code == 403


def test_manager_can_create_update_and_deactivate_customer(client, manager_headers):
    created = client.post("/api/v1/customers/", headers=manager_headers, json=CUSTOMER)
    assert created.status_code == 200, created.text
    customer = created.json()
    assert customer["points_balance"] == 0

    updated = client.put(
        f"/api/v1/customers/{customer['id']}",
        headers=manager_headers,
        json={"phone": "555-0199"},
    )
    assert updated.status_code == 200
    assert updated.json()["phone"] == "555-0199"

    deactivated = client.delete(
        f"/api/v1/customers/{customer['id']}", headers=manager_headers
    )
    assert deactivated.status_code == 200
    fetched = client.get(
        f"/api/v1/customers/{customer['id']}", headers=manager_headers
    ).json()
    assert fetched["is_active"] is False


def test_inactive_customer_cannot_order(
    client, manager_headers, make_product, open_drawer
):
    customer = client.post(
        "/api/v1/customers/", headers=manager_headers, json=CUSTOMER
    ).json()
    client.delete(f"/api/v1/customers/{customer['id']}", headers=manager_headers)
    product = make_product(
        manager_headers, name="Inactive Cust", sku="SKU-INCUST", price=10.0
    )
    open_drawer(manager_headers)

    order = client.post(
        "/api/v1/orders/",
        headers=manager_headers,
        json={**order_payload(product["id"]), "customer_id": customer["id"]},
    )
    assert order.status_code == 400
    assert order.json()["detail"] == "Customer is inactive"


def test_loyalty_points_earned_and_redeemed(
    client, manager_headers, make_product, open_drawer
):
    customer = client.post(
        "/api/v1/customers/",
        headers=manager_headers,
        json={"name": "Loyal", "email": "loyal@example.com"},
    ).json()
    product = make_product(
        manager_headers, name="Loyal Item", sku="SKU-LOYAL", price=100.0
    )
    open_drawer(manager_headers)

    first = client.post(
        "/api/v1/orders/",
        headers=manager_headers,
        json={**order_payload(product["id"]), "customer_id": customer["id"]},
    )
    assert first.status_code == 200, first.text
    client.post(
        f"/api/v1/orders/{first.json()['id']}/payments",
        headers=manager_headers,
        json={"payment_method": "card", "amount": 100.0},
    )

    after_earn = client.get(
        f"/api/v1/customers/{customer['id']}", headers=manager_headers
    ).json()
    assert after_earn["points_balance"] == 100

    second = client.post(
        "/api/v1/orders/",
        headers=manager_headers,
        json={
            **order_payload(product["id"]),
            "customer_id": customer["id"],
            "redeem_points": 40,
        },
    )
    assert second.status_code == 200, second.text
    assert second.json()["total_amount"] == 60.0

    after_redeem = client.get(
        f"/api/v1/customers/{customer['id']}", headers=manager_headers
    ).json()
    assert after_redeem["points_balance"] == 60

    txns = client.get(
        f"/api/v1/customers/{customer['id']}/loyalty-transactions",
        headers=manager_headers,
    )
    assert txns.status_code == 200
    types = {t["transaction_type"] for t in txns.json()}
    assert types == {"earn", "redeem"}


def test_customer_orders_listing(client, manager_headers, make_product, open_drawer):
    customer = client.post(
        "/api/v1/customers/",
        headers=manager_headers,
        json={"name": "History", "email": "history@example.com"},
    ).json()
    product = make_product(
        manager_headers, name="Hist Item", sku="SKU-HIST", price=10.0
    )
    open_drawer(manager_headers)
    client.post(
        "/api/v1/orders/",
        headers=manager_headers,
        json={**order_payload(product["id"]), "customer_id": customer["id"]},
    )

    orders = client.get(
        f"/api/v1/customers/{customer['id']}/orders", headers=manager_headers
    )
    assert orders.status_code == 200
    assert len(orders.json()) == 1


def test_customer_404s(client, manager_headers):
    resp = client.get("/api/v1/customers/99999", headers=manager_headers)
    assert resp.status_code == 404
