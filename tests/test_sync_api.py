"""Integration tests for the offline sync batch endpoint."""

from conftest import order_payload


def _batch(client, headers, events):
    resp = client.post(
        "/api/v1/sync/events/batch",
        headers=headers,
        json={"events": events},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["results"]


def test_batch_creates_order_and_reports_success(
    client, cashier_headers, make_product, open_drawer, manager_headers
):
    product = make_product(
        manager_headers, name="Sync Item", sku="SKU-SYNC", price=30.0
    )
    open_drawer(cashier_headers)

    event = {
        "client_event_id": "evt-1",
        "event_type": "order_create",
        "idempotency_key": "sync-ik-1",
        "payload": {"items": [{"product_id": product["id"], "quantity": 2}]},
    }
    results = _batch(client, cashier_headers, [event])

    assert results[0]["status"] == "success"
    assert results[0]["resource_type"] == "order"
    assert results[0]["resource_id"] is not None

    orders = client.get("/api/v1/orders/", headers=cashier_headers).json()
    assert len(orders) == 1
    assert orders[0]["total_amount"] == 60.0

    products = client.get("/api/v1/products/", headers=cashier_headers).json()
    assert next(p for p in products if p["id"] == product["id"])["stock_quantity"] == 8


def test_replayed_event_is_duplicate_with_same_resource(
    client, cashier_headers, make_product, open_drawer, manager_headers
):
    product = make_product(manager_headers, name="Dup Item", sku="SKU-DUP", price=10.0)
    open_drawer(cashier_headers)

    event = {
        "client_event_id": "evt-dup",
        "event_type": "order_create",
        "idempotency_key": "sync-ik-dup",
        "payload": {"items": [{"product_id": product["id"], "quantity": 1}]},
    }
    first = _batch(client, cashier_headers, [event])
    replay = _batch(client, cashier_headers, [event])

    assert first[0]["status"] == "success"
    assert replay[0]["status"] == "duplicate"
    assert replay[0]["resource_id"] == first[0]["resource_id"]

    orders = client.get("/api/v1/orders/", headers=cashier_headers).json()
    assert len(orders) == 1


def test_invalid_event_payload_marked_failed(client, cashier_headers):
    event = {
        "client_event_id": "evt-bad",
        "event_type": "order_create",
        "idempotency_key": "sync-ik-bad",
        "payload": {"items": "not-a-list"},
    }
    results = _batch(client, cashier_headers, [event])

    assert results[0]["status"] == "failed"
    assert results[0]["message"]


def test_unsupported_event_type_marked_failed(client, cashier_headers):
    event = {
        "client_event_id": "evt-unknown",
        "event_type": "teleport_user",
        "idempotency_key": "sync-ik-unknown",
        "payload": {},
    }
    results = _batch(client, cashier_headers, [event])

    assert results[0]["status"] == "failed"


def test_batch_processes_mixed_events_independently(
    client, cashier_headers, make_product, open_drawer, manager_headers
):
    product = make_product(manager_headers, name="Mixed", sku="SKU-MIX", price=40.0)
    open_drawer(cashier_headers)

    order_event = {
        "client_event_id": "evt-mix-1",
        "event_type": "order_create",
        "idempotency_key": "sync-ik-mix",
        "payload": {"items": [{"product_id": product["id"], "quantity": 1}]},
    }
    results = _batch(client, cashier_headers, [order_event])
    order_id = results[0]["resource_id"]

    payment_event = {
        "client_event_id": "evt-mix-2",
        "event_type": "order_add_payment",
        "idempotency_key": "sync-pay-mix",
        "payload": {"order_id": order_id, "payment_method": "card", "amount": 40.0},
    }
    results = _batch(client, cashier_headers, [payment_event])

    assert results[0]["status"] == "success"
    assert results[0]["resource_type"] == "payment"

    receipt = client.get(
        f"/api/v1/orders/{order_id}/receipt", headers=cashier_headers
    ).json()
    assert receipt["status"] == "serving"


def test_catalog_full_sync_returns_all_rows(client, manager_headers, make_product):
    headers = manager_headers
    product = make_product(
        headers, name="Sync Product", sku="SYNC-1", price=9.99, stock=5
    )

    resp = client.get("/api/v1/sync/catalog", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["server_time"]
    assert body["since"] is None
    product_ids = {p["id"] for p in body["products"]}
    assert product["id"] in product_ids
    assert any(c for c in body["categories"])


def test_catalog_sync_includes_image_urls(client, manager_headers, make_product):
    headers = manager_headers
    product = make_product(
        headers, name="Sync Photo", sku="SYNC-PHOTO", price=9.99, stock=5
    )
    import io

    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), (10, 120, 200)).save(buffer, format="PNG")
    uploaded = client.post(
        f"/api/v1/products/{product['id']}/image",
        headers=headers,
        files={"file": ("p.png", buffer.getvalue(), "image/png")},
    ).json()

    resp = client.get("/api/v1/sync/catalog", headers=headers)
    assert resp.status_code == 200, resp.text
    synced = next(p for p in resp.json()["products"] if p["id"] == product["id"])
    assert synced["image_url"] == uploaded["image_url"]
    assert synced["thumbnail_url"] == uploaded["thumbnail_url"]


def test_catalog_delta_returns_only_changed(client, manager_headers, make_product):
    headers = manager_headers
    product = make_product(
        headers, name="Delta Product", sku="SYNC-2", price=5.0, stock=3
    )

    resp = client.get("/api/v1/sync/catalog", headers=headers)
    watermark = resp.json()["server_time"]

    # change the product -> updated_at bumps past the watermark
    resp = client.put(
        f"/api/v1/products/{product['id']}", headers=headers, json={"price": 6.0}
    )
    assert resp.status_code == 200, resp.text

    resp = client.get(f"/api/v1/sync/catalog?since={watermark}", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert any(p["id"] == product["id"] for p in body["products"]), body["products"]

    # stale watermark from the future -> nothing
    resp = client.get(
        "/api/v1/sync/catalog?since=2999-01-01T00:00:00Z", headers=headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["products"] == []


def test_sync_event_status_lists_processed_events(client, auth_factory):
    headers = auth_factory.user("sync-events@example.com")
    client.post(
        "/api/v1/sync/events/batch",
        headers=headers,
        json={
            "events": [
                {
                    "client_event_id": "st-1",
                    "event_type": "note",
                    "idempotency_key": "stk-1",
                    "payload": {"text": "hello"},
                },
            ]
        },
    )
    resp = client.get("/api/v1/sync/events", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] >= 1
    assert body["items"][0]["client_event_id"] == "st-1"


def test_sync_event_status_forbids_other_user_visibility(client, auth_factory):
    headers = auth_factory.user("sync-owner@example.com")
    other = auth_factory.user("sync-other@example.com")
    _ = other
    resp = client.get("/api/v1/sync/events?user_id=999", headers=headers)
    assert resp.status_code == 403, resp.text
