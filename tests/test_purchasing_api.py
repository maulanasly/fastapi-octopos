"""Integration tests for the purchasing API: suppliers, purchase orders,
receiving, and invoice review/approval."""


def _make_supplier(client, manager_headers, name="Acme Supplies"):
    resp = client.post(
        "/api/v1/purchasing/suppliers",
        headers=manager_headers,
        json={"name": name, "contact_email": "sales@acme.test", "phone": "555-0000"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _make_po(
    client, manager_headers, supplier_id, product_id, quantity=10, unit_cost=5.0
):
    resp = client.post(
        "/api/v1/purchasing/orders",
        headers=manager_headers,
        json={
            "supplier_id": supplier_id,
            "notes": "restock",
            "items": [
                {
                    "product_id": product_id,
                    "quantity_ordered": quantity,
                    "unit_cost": unit_cost,
                }
            ],
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _receive_all(client, manager_headers, po, quantity=10):
    resp = client.post(
        f"/api/v1/purchasing/orders/{po['id']}/receive",
        headers=manager_headers,
        json={
            "items": [
                {
                    "purchase_order_item_id": po["items"][0]["id"],
                    "quantity_received": quantity,
                }
            ]
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_supplier_crud(client, manager_headers):
    supplier = _make_supplier(client, manager_headers)
    assert supplier["is_active"] is True

    updated = client.put(
        f"/api/v1/purchasing/suppliers/{supplier['id']}",
        headers=manager_headers,
        json={"phone": "555-9999"},
    )
    assert updated.status_code == 200
    assert updated.json()["phone"] == "555-9999"

    suppliers = client.get(
        "/api/v1/purchasing/suppliers?active_only=true", headers=manager_headers
    ).json()
    assert any(s["id"] == supplier["id"] for s in suppliers)


def test_purchase_order_lifecycle_restores_stock(
    client, cashier_headers, manager_headers, make_product
):
    product = make_product(
        manager_headers, name="Procure Me", sku="SKU-PROC", price=10.0, stock=10
    )
    supplier = _make_supplier(client, manager_headers)

    po = _make_po(client, manager_headers, supplier["id"], product["id"])
    assert po["status"] == "draft"
    assert po["total_estimated_amount"] == 50.0

    ordered = client.post(
        f"/api/v1/purchasing/orders/{po['id']}/mark-ordered",
        headers=manager_headers,
    )
    assert ordered.status_code == 200, ordered.text
    assert ordered.json()["status"] == "ordered"

    received = _receive_all(client, manager_headers, po)
    assert received["status"] == "received"

    products = client.get("/api/v1/products/", headers=cashier_headers).json()
    updated = next(p for p in products if p["id"] == product["id"])
    assert updated["stock_quantity"] == 20

    movements = client.get(
        "/api/v1/inventory/movements", headers=cashier_headers
    ).json()
    receipt_movements = [
        m for m in movements if m["movement_type"] == "purchase_receipt"
    ]
    assert len(receipt_movements) == 1
    assert receipt_movements[0]["quantity_delta"] == 10


def test_receive_over_ordered_quantity_rejected(client, manager_headers, make_product):
    product = make_product(manager_headers, name="Over Recv", sku="SKU-OVR", price=10.0)
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(client, manager_headers, supplier["id"], product["id"], quantity=10)

    resp = client.post(
        f"/api/v1/purchasing/orders/{po['id']}/receive",
        headers=manager_headers,
        json={
            "items": [
                {
                    "purchase_order_item_id": po["items"][0]["id"],
                    "quantity_received": 11,
                }
            ]
        },
    )
    assert resp.status_code == 400
    assert "exceeds remaining quantity" in resp.json()["detail"]


def test_cancel_purchase_order(client, manager_headers, make_product):
    product = make_product(manager_headers, name="Cancel PO", sku="SKU-CPO", price=10.0)
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(client, manager_headers, supplier["id"], product["id"])

    resp = client.post(
        f"/api/v1/purchasing/orders/{po['id']}/cancel", headers=manager_headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "cancelled"

    cancel_again = client.post(
        f"/api/v1/purchasing/orders/{po['id']}/cancel", headers=manager_headers
    )
    assert cancel_again.status_code == 400


def test_invoice_review_and_approval_flow(client, manager_headers, make_product):
    product = make_product(
        manager_headers, name="Invoice Me", sku="SKU-INV", price=10.0
    )
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(
        client,
        manager_headers,
        supplier["id"],
        product["id"],
        quantity=10,
        unit_cost=5.0,
    )
    client.post(
        f"/api/v1/purchasing/orders/{po['id']}/mark-ordered", headers=manager_headers
    )
    _receive_all(client, manager_headers, po)

    created = client.post(
        "/api/v1/purchasing/invoices",
        headers=manager_headers,
        json={
            "purchase_order_id": po["id"],
            "invoice_number": "INV-001",
            "items": [
                {
                    "purchase_order_item_id": po["items"][0]["id"],
                    "billed_quantity": 10,
                    "billed_unit_cost": 5.0,
                }
            ],
        },
    )
    assert created.status_code == 200, created.text
    invoice = created.json()
    assert invoice["status"] == "draft"
    assert invoice["total_amount"] == 50.0
    assert invoice["has_quantity_variance"] is False
    assert invoice["has_price_variance"] is False

    reviewed = client.post(
        f"/api/v1/purchasing/invoices/{invoice['id']}/submit-review",
        headers=manager_headers,
        json={"review_note": "looks good"},
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["status"] == "pending_review"

    approved = client.post(
        f"/api/v1/purchasing/invoices/{invoice['id']}/approve",
        headers=manager_headers,
        json={},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"

    summary = client.get(
        "/api/v1/reports/purchase-invoices", headers=manager_headers
    ).json()
    assert summary["approved_count"] == 1
    assert summary["approved_total"] == 50.0
    assert summary["invoice_count"] == 1


def test_invoice_fractional_unit_cost_no_float_drift(
    client, manager_headers, make_product
):
    product = make_product(manager_headers, name="Frac Cost", sku="SKU-FRC", price=10.0)
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(
        client,
        manager_headers,
        supplier["id"],
        product["id"],
        quantity=3,
        unit_cost=0.1,
    )
    client.post(
        f"/api/v1/purchasing/orders/{po['id']}/mark-ordered", headers=manager_headers
    )
    _receive_all(client, manager_headers, po, quantity=3)

    created = client.post(
        "/api/v1/purchasing/invoices",
        headers=manager_headers,
        json={
            "purchase_order_id": po["id"],
            "invoice_number": "INV-FRC",
            "items": [
                {
                    "purchase_order_item_id": po["items"][0]["id"],
                    "billed_quantity": 3,
                    "billed_unit_cost": 0.1,
                }
            ],
        },
    )
    assert created.status_code == 200, created.text
    invoice = created.json()
    assert invoice["total_amount"] == 0.3
    assert invoice["variance_amount"] == 0.0
    assert invoice["has_price_variance"] is False


def test_invoice_price_variance_flagged(client, manager_headers, make_product):
    product = make_product(manager_headers, name="Variance", sku="SKU-VAR", price=10.0)
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(
        client,
        manager_headers,
        supplier["id"],
        product["id"],
        quantity=10,
        unit_cost=5.0,
    )
    client.post(
        f"/api/v1/purchasing/orders/{po['id']}/mark-ordered", headers=manager_headers
    )
    _receive_all(client, manager_headers, po)

    created = client.post(
        "/api/v1/purchasing/invoices",
        headers=manager_headers,
        json={
            "purchase_order_id": po["id"],
            "invoice_number": "INV-VAR",
            "items": [
                {
                    "purchase_order_item_id": po["items"][0]["id"],
                    "billed_quantity": 10,
                    "billed_unit_cost": 6.0,
                }
            ],
        },
    )
    assert created.status_code == 200, created.text
    invoice = created.json()
    assert invoice["has_price_variance"] is True
    assert invoice["variance_amount"] == 10.0


def test_duplicate_invoice_number_rejected(client, manager_headers, make_product):
    product = make_product(manager_headers, name="Dup Inv", sku="SKU-DINV", price=10.0)
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(client, manager_headers, supplier["id"], product["id"])
    client.post(
        f"/api/v1/purchasing/orders/{po['id']}/mark-ordered", headers=manager_headers
    )
    _receive_all(client, manager_headers, po)

    payload = {
        "purchase_order_id": po["id"],
        "invoice_number": "INV-DUP",
        "items": [
            {
                "purchase_order_item_id": po["items"][0]["id"],
                "billed_quantity": 10,
                "billed_unit_cost": 5.0,
            }
        ],
    }
    created = client.post(
        "/api/v1/purchasing/invoices", headers=manager_headers, json=payload
    )
    assert created.status_code == 200
    dup = client.post(
        "/api/v1/purchasing/invoices", headers=manager_headers, json=payload
    )
    assert dup.status_code == 400
    assert "already exists" in dup.json()["detail"]


def test_cashier_cannot_approve_invoices(
    client, manager_headers, cashier_headers, make_product
):
    product = make_product(
        manager_headers, name="Approve Gate", sku="SKU-AG", price=10.0
    )
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(client, manager_headers, supplier["id"], product["id"])
    client.post(
        f"/api/v1/purchasing/orders/{po['id']}/mark-ordered", headers=manager_headers
    )
    _receive_all(client, manager_headers, po)
    invoice = client.post(
        "/api/v1/purchasing/invoices",
        headers=manager_headers,
        json={
            "purchase_order_id": po["id"],
            "invoice_number": "INV-GATE",
            "items": [
                {
                    "purchase_order_item_id": po["items"][0]["id"],
                    "billed_quantity": 10,
                    "billed_unit_cost": 5.0,
                }
            ],
        },
    ).json()

    resp = client.post(
        f"/api/v1/purchasing/invoices/{invoice['id']}/approve",
        headers=cashier_headers,
        json={},
    )
    assert resp.status_code == 403
