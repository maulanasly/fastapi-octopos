"""Serving queue API: auto-queue on payment, strict state machine, tenant
isolation, permissions, and the SSE event feed."""

import json

import _tenant_mode
import pytest
from conftest import order_payload


def _create_and_pay(client, headers, product_id, amount=None):
    order = client.post(
        "/api/v1/orders/",
        headers=headers,
        json=order_payload(product_id, quantity=2),
    )
    assert order.status_code == 200, order.text
    order = order.json()
    total = order["total_amount"] if amount is None else amount
    resp = client.post(
        f"/api/v1/orders/{order['id']}/payments",
        headers=headers,
        json={"payment_method": "cash", "amount": total},
    )
    assert resp.status_code == 200, resp.text
    return order


def test_paid_order_enters_serving_queue(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    product = make_product(manager_headers, name="Q Item", sku="SKU-Q1", price=10.0)
    open_drawer(cashier_headers)
    order = _create_and_pay(client, cashier_headers, product["id"])

    assert order["serving_status"] == "none"  # pre-payment
    receipt = client.get(
        f"/api/v1/orders/{order['id']}/receipt", headers=cashier_headers
    ).json()
    assert receipt["serving_status"] == "queued"
    # Paid orders are in the serving pipeline, not yet completed.
    assert receipt["status"] == "serving"

    queue = client.get("/api/v1/orders/serving/", headers=cashier_headers)
    assert queue.status_code == 200, queue.text
    body = queue.json()
    assert queue.headers["x-total-count"] == "1"
    assert body[0]["id"] == order["id"]
    assert body[0]["serving_status"] == "queued"
    assert len(body[0]["items"]) == 1


def test_unpaid_order_not_in_queue(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    product = make_product(manager_headers, name="Not Paid", sku="SKU-NP", price=10.0)
    open_drawer(cashier_headers)
    order = client.post(
        "/api/v1/orders/",
        headers=cashier_headers,
        json=order_payload(product["id"], quantity=1),
    )
    assert order.status_code == 200, order.text

    queue = client.get("/api/v1/orders/serving/", headers=cashier_headers)
    assert queue.json() == []


def test_serving_transitions_happy_path(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    product = make_product(manager_headers, name="Transit", sku="SKU-TR", price=10.0)
    open_drawer(cashier_headers)
    order = _create_and_pay(client, cashier_headers, product["id"])

    started = client.post(
        f"/api/v1/orders/serving/{order['id']}/start", headers=cashier_headers
    )
    assert started.status_code == 200, started.text
    assert started.json()["serving_status"] == "preparing"
    assert started.json()["preparing_at"] is not None

    ready = client.post(
        f"/api/v1/orders/serving/{order['id']}/ready", headers=cashier_headers
    )
    assert ready.status_code == 200, ready.text
    assert ready.json()["serving_status"] == "ready"
    assert ready.json()["ready_at"] is not None

    served = client.post(
        f"/api/v1/orders/serving/{order['id']}/serve", headers=cashier_headers
    )
    assert served.status_code == 200, served.text
    assert served.json()["serving_status"] == "served"
    assert served.json()["served_at"] is not None
    assert served.json()["status"] == "completed"

    queue = client.get("/api/v1/orders/serving/", headers=cashier_headers)
    assert queue.json() == []


def test_serve_allowed_from_preparing(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    product = make_product(manager_headers, name="Skip", sku="SKU-SK", price=10.0)
    open_drawer(cashier_headers)
    order = _create_and_pay(client, cashier_headers, product["id"])

    client.post(f"/api/v1/orders/serving/{order['id']}/start", headers=cashier_headers)
    served = client.post(
        f"/api/v1/orders/serving/{order['id']}/serve", headers=cashier_headers
    )
    assert served.status_code == 200, served.text
    assert served.json()["serving_status"] == "served"


def test_invalid_transitions_rejected(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    product = make_product(manager_headers, name="Strict", sku="SKU-ST", price=10.0)
    open_drawer(cashier_headers)
    order = _create_and_pay(client, cashier_headers, product["id"])

    # queued -> served directly is not allowed
    resp = client.post(
        f"/api/v1/orders/serving/{order['id']}/serve", headers=cashier_headers
    )
    assert resp.status_code == 400
    assert "queued" in resp.json()["detail"]

    # ready -> preparing (backwards) is not allowed
    client.post(f"/api/v1/orders/serving/{order['id']}/start", headers=cashier_headers)
    client.post(f"/api/v1/orders/serving/{order['id']}/ready", headers=cashier_headers)
    resp = client.post(
        f"/api/v1/orders/serving/{order['id']}/start", headers=cashier_headers
    )
    assert resp.status_code == 400


def test_serving_rejects_unpaid_and_cancelled_orders(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    product = make_product(manager_headers, name="Unpaid", sku="SKU-UP", price=10.0)
    open_drawer(cashier_headers)
    unpaid = client.post(
        "/api/v1/orders/",
        headers=cashier_headers,
        json=order_payload(product["id"], quantity=1),
    ).json()

    resp = client.post(
        f"/api/v1/orders/serving/{unpaid['id']}/start", headers=cashier_headers
    )
    assert resp.status_code == 400
    assert "serving" in resp.json()["detail"]

    paid = _create_and_pay(client, cashier_headers, product["id"])
    client.post(f"/api/v1/orders/{paid['id']}/cancel", headers=cashier_headers)
    resp = client.post(
        f"/api/v1/orders/serving/{paid['id']}/start", headers=cashier_headers
    )
    assert resp.status_code == 400


def test_serving_status_filter(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    product = make_product(manager_headers, name="Filter", sku="SKU-FL", price=10.0)
    open_drawer(cashier_headers)
    a = _create_and_pay(client, cashier_headers, product["id"])
    b = _create_and_pay(client, cashier_headers, product["id"])

    client.post(f"/api/v1/orders/serving/{a['id']}/start", headers=cashier_headers)

    ready = client.get(
        "/api/v1/orders/serving/?status=preparing", headers=cashier_headers
    )
    assert [o["id"] for o in ready.json()] == [a["id"]]

    queued = client.get(
        "/api/v1/orders/serving/?status=queued", headers=cashier_headers
    )
    assert [o["id"] for o in queued.json()] == [b["id"]]


def test_serving_queue_oldest_first(
    client, cashier_headers, manager_headers, make_product, open_drawer
):
    product = make_product(manager_headers, name="FIFO", sku="SKU-FO", price=10.0)
    open_drawer(cashier_headers)
    a = _create_and_pay(client, cashier_headers, product["id"])
    b = _create_and_pay(client, cashier_headers, product["id"])

    queue = client.get("/api/v1/orders/serving/", headers=cashier_headers)
    assert [o["id"] for o in queue.json()] == [a["id"], b["id"]]


def test_serving_requires_permission(client, auth_factory, db):
    """A user without orders:manage cannot touch the queue."""
    user = auth_factory.register("roleless@example.com")

    from app.models.user import User

    db_user = db.get(User, user["id"])
    db_user.roles = []
    db.commit()

    headers = auth_factory.login("roleless@example.com")
    assert client.get("/api/v1/orders/serving/", headers=headers).status_code == 403
    resp = client.post("/api/v1/orders/serving/1/start", headers=headers)
    assert resp.status_code == 403


def test_serving_hub_fanout_is_tenant_scoped():
    """ServingHub delivers events only to subscribers of the same tenant."""
    import asyncio

    from app.services.serving import ServingHub

    async def scenario():
        hub = ServingHub()
        wrapper = hub.subscribe(7)
        hub.publish(7, {"order_id": 1, "serving_status": "preparing"})
        hub.publish(8, {"order_id": 2, "serving_status": "ready"})
        event = await wrapper.get(1.0)
        hub.unsubscribe(7, wrapper)
        return event

    event = asyncio.run(scenario())
    assert event == {"order_id": 1, "serving_status": "preparing"}
