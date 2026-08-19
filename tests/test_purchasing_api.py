"""Integration tests for the purchasing API: suppliers, purchase orders,
receiving, invoice review/approval, and supplier payments."""


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


def _submit_po(client, manager_headers, po):
    resp = client.post(
        f"/api/v1/purchasing/orders/{po['id']}/submit-review",
        headers=manager_headers,
        json={"review_note": "please approve"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _approve_po(client, admin_headers, po):
    resp = client.post(
        f"/api/v1/purchasing/orders/{po['id']}/mark-ordered",
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _order_po(client, manager_headers, admin_headers, po):
    """Submit for review (requester) then approve (approver)."""
    _submit_po(client, manager_headers, po)
    return _approve_po(client, admin_headers, po)


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


def _make_invoice(
    client, manager_headers, po, invoice_number="INV-001", quantity=10, unit_cost=5.0
):
    resp = client.post(
        "/api/v1/purchasing/invoices",
        headers=manager_headers,
        json={
            "purchase_order_id": po["id"],
            "invoice_number": invoice_number,
            "items": [
                {
                    "purchase_order_item_id": po["items"][0]["id"],
                    "billed_quantity": quantity,
                    "billed_unit_cost": unit_cost,
                }
            ],
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _submit_invoice(client, manager_headers, invoice):
    resp = client.post(
        f"/api/v1/purchasing/invoices/{invoice['id']}/submit-review",
        headers=manager_headers,
        json={"review_note": "looks good"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _approve_invoice(client, admin_headers, invoice):
    resp = client.post(
        f"/api/v1/purchasing/invoices/{invoice['id']}/approve",
        headers=admin_headers,
        json={},
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
    client, cashier_headers, manager_headers, admin_headers, make_product
):
    product = make_product(
        manager_headers, name="Procure Me", sku="SKU-PROC", price=10.0, stock=10
    )
    supplier = _make_supplier(client, manager_headers)

    po = _make_po(client, manager_headers, supplier["id"], product["id"])
    assert po["status"] == "draft"
    assert po["total_estimated_amount"] == 50.0

    ordered = _order_po(client, manager_headers, admin_headers, po)
    assert ordered["status"] == "ordered"

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


def test_receive_over_ordered_quantity_rejected(
    client, manager_headers, admin_headers, make_product
):
    product = make_product(manager_headers, name="Over Recv", sku="SKU-OVR", price=10.0)
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(client, manager_headers, supplier["id"], product["id"], quantity=10)
    _order_po(client, manager_headers, admin_headers, po)

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


def test_receive_draft_po_rejected(client, manager_headers, make_product):
    product = make_product(
        manager_headers, name="Draft Recv", sku="SKU-DRV", price=10.0
    )
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(client, manager_headers, supplier["id"], product["id"])

    resp = client.post(
        f"/api/v1/purchasing/orders/{po['id']}/receive",
        headers=manager_headers,
        json={
            "items": [
                {
                    "purchase_order_item_id": po["items"][0]["id"],
                    "quantity_received": 1,
                }
            ]
        },
    )
    assert resp.status_code == 400
    assert "draft" in resp.json()["detail"]


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


def test_purchase_order_review_and_reject_flow(
    client, manager_headers, admin_headers, make_product
):
    product = make_product(manager_headers, name="Reject PO", sku="SKU-RPO", price=10.0)
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(client, manager_headers, supplier["id"], product["id"])

    pending = _submit_po(client, manager_headers, po)
    assert pending["status"] == "pending_review"

    rejected = client.post(
        f"/api/v1/purchasing/orders/{po['id']}/reject",
        headers=admin_headers,
        json={"review_note": "not now"},
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "rejected"

    receive = client.post(
        f"/api/v1/purchasing/orders/{po['id']}/receive",
        headers=manager_headers,
        json={
            "items": [
                {
                    "purchase_order_item_id": po["items"][0]["id"],
                    "quantity_received": 1,
                }
            ]
        },
    )
    assert receive.status_code == 400
    assert "rejected" in receive.json()["detail"]


def test_manager_cannot_approve_own_or_other_po(
    client, manager_headers, admin_headers, make_product
):
    product = make_product(manager_headers, name="No Appr", sku="SKU-NAP", price=10.0)
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(client, manager_headers, supplier["id"], product["id"])
    _submit_po(client, manager_headers, po)

    resp = client.post(
        f"/api/v1/purchasing/orders/{po['id']}/mark-ordered",
        headers=manager_headers,
    )
    assert resp.status_code == 403
    assert "purchasing:approve" in resp.json()["detail"]


def test_self_approval_rejected(client, manager_headers, admin_headers, make_product):
    product = make_product(manager_headers, name="Self Appr", sku="SKU-SAP", price=10.0)
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(client, manager_headers, supplier["id"], product["id"])
    _submit_po(client, manager_headers, po)

    # The admin user cannot approve a PO they created themselves.
    own_po = client.post(
        "/api/v1/purchasing/orders",
        headers=admin_headers,
        json={
            "supplier_id": supplier["id"],
            "items": [
                {
                    "product_id": product["id"],
                    "quantity_ordered": 5,
                    "unit_cost": 5.0,
                }
            ],
        },
    ).json()
    client.post(
        f"/api/v1/purchasing/orders/{own_po['id']}/submit-review",
        headers=admin_headers,
        json={},
    )
    self_approve = client.post(
        f"/api/v1/purchasing/orders/{own_po['id']}/mark-ordered",
        headers=admin_headers,
    )
    assert self_approve.status_code == 403
    assert "you created" in self_approve.json()["detail"]

    # ...but the manager's PO can be approved by the admin user.
    cross_approve = client.post(
        f"/api/v1/purchasing/orders/{po['id']}/mark-ordered",
        headers=admin_headers,
    )
    assert cross_approve.status_code == 200, cross_approve.text
    assert cross_approve.json()["status"] == "ordered"


def test_invoice_review_and_approval_flow(
    client, manager_headers, admin_headers, make_product
):
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
    _order_po(client, manager_headers, admin_headers, po)
    _receive_all(client, manager_headers, po)

    invoice = _make_invoice(client, manager_headers, po)
    assert invoice["status"] == "draft"
    assert invoice["total_amount"] == 50.0
    assert invoice["has_quantity_variance"] is False
    assert invoice["has_price_variance"] is False

    reviewed = _submit_invoice(client, manager_headers, invoice)
    assert reviewed["status"] == "pending_review"

    approved = _approve_invoice(client, admin_headers, invoice)
    assert approved["status"] == "approved"

    summary = client.get(
        "/api/v1/reports/purchase-invoices", headers=manager_headers
    ).json()
    assert summary["approved_count"] == 1
    assert summary["approved_total"] == 50.0
    assert summary["invoice_count"] == 1


def test_self_invoice_approval_rejected(
    client, manager_headers, admin_headers, make_product
):
    product = make_product(manager_headers, name="Self Inv", sku="SKU-SINV", price=10.0)
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(client, manager_headers, supplier["id"], product["id"])
    _order_po(client, manager_headers, admin_headers, po)
    _receive_all(client, manager_headers, po)

    invoice = _make_invoice(client, admin_headers, po, invoice_number="INV-SELF")
    _submit_invoice(client, admin_headers, invoice)

    resp = client.post(
        f"/api/v1/purchasing/invoices/{invoice['id']}/approve",
        headers=admin_headers,
        json={},
    )
    assert resp.status_code == 403
    assert "you created" in resp.json()["detail"]


def test_invoice_fractional_unit_cost_no_float_drift(
    client, manager_headers, admin_headers, make_product
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
    _order_po(client, manager_headers, admin_headers, po)
    _receive_all(client, manager_headers, po, quantity=3)

    invoice = _make_invoice(
        client,
        manager_headers,
        po,
        invoice_number="INV-FRC",
        quantity=3,
        unit_cost=0.1,
    )
    assert invoice["total_amount"] == 0.3
    assert invoice["variance_amount"] == 0.0
    assert invoice["has_price_variance"] is False


def test_invoice_price_variance_flagged(
    client, manager_headers, admin_headers, make_product
):
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
    _order_po(client, manager_headers, admin_headers, po)
    _receive_all(client, manager_headers, po)

    invoice = _make_invoice(
        client, manager_headers, po, invoice_number="INV-VAR", unit_cost=6.0
    )
    assert invoice["has_price_variance"] is True
    assert invoice["variance_amount"] == 10.0


def test_duplicate_invoice_number_rejected(
    client, manager_headers, admin_headers, make_product
):
    product = make_product(manager_headers, name="Dup Inv", sku="SKU-DINV", price=10.0)
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(client, manager_headers, supplier["id"], product["id"])
    _order_po(client, manager_headers, admin_headers, po)
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
    client, manager_headers, admin_headers, cashier_headers, make_product
):
    product = make_product(
        manager_headers, name="Approve Gate", sku="SKU-AG", price=10.0
    )
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(client, manager_headers, supplier["id"], product["id"])
    _order_po(client, manager_headers, admin_headers, po)
    _receive_all(client, manager_headers, po)
    invoice = _make_invoice(client, manager_headers, po, invoice_number="INV-GATE")

    resp = client.post(
        f"/api/v1/purchasing/invoices/{invoice['id']}/approve",
        headers=cashier_headers,
        json={},
    )
    assert resp.status_code == 403


def test_approve_invoice_updates_product_unit_cost(
    client, manager_headers, admin_headers, make_product
):
    product = make_product(manager_headers, name="Cost Basis", sku="SKU-CB", price=10.0)
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(client, manager_headers, supplier["id"], product["id"], unit_cost=5.0)
    _order_po(client, manager_headers, admin_headers, po)
    _receive_all(client, manager_headers, po)

    invoice = _make_invoice(
        client, manager_headers, po, invoice_number="INV-COST", unit_cost=6.5
    )
    _submit_invoice(client, manager_headers, invoice)
    approved = _approve_invoice(client, admin_headers, invoice)
    assert approved["status"] == "approved"

    products = client.get("/api/v1/products/", headers=manager_headers).json()
    updated = next(p for p in products if p["id"] == product["id"])
    assert updated["unit_cost"] == 6.5


def test_supplier_payment_lifecycle(
    client, manager_headers, admin_headers, make_product
):
    product = make_product(manager_headers, name="Pay Me", sku="SKU-PAY", price=10.0)
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(client, manager_headers, supplier["id"], product["id"])
    _order_po(client, manager_headers, admin_headers, po)
    _receive_all(client, manager_headers, po)
    invoice = _make_invoice(client, manager_headers, po, invoice_number="INV-PAY")
    _submit_invoice(client, manager_headers, invoice)
    _approve_invoice(client, admin_headers, invoice)

    created = client.post(
        "/api/v1/purchasing/payments",
        headers=manager_headers,
        json={
            "supplier_id": supplier["id"],
            "invoice_id": invoice["id"],
            "amount": 30.0,
            "payment_method": "transfer",
            "reference": "TRX-001",
        },
    )
    assert created.status_code == 200, created.text
    payment = created.json()
    assert payment["status"] == "draft"
    assert payment["amount"] == 30.0

    submitted = client.post(
        f"/api/v1/purchasing/payments/{payment['id']}/submit-review",
        headers=manager_headers,
        json={"review_note": "paid first part"},
    )
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["status"] == "pending_review"

    approved = client.post(
        f"/api/v1/purchasing/payments/{payment['id']}/approve",
        headers=admin_headers,
        json={},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"

    summary = client.get(
        "/api/v1/reports/supplier-payments", headers=manager_headers
    ).json()
    assert summary["payment_count"] == 1
    assert summary["approved_count"] == 1
    assert summary["approved_total"] == 30.0
    assert summary["outstanding_payable"] == 20.0


def test_supplier_payment_partial_and_overpayment(
    client, manager_headers, admin_headers, make_product
):
    product = make_product(manager_headers, name="Pay Part", sku="SKU-PPT", price=10.0)
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(client, manager_headers, supplier["id"], product["id"])
    _order_po(client, manager_headers, admin_headers, po)
    _receive_all(client, manager_headers, po)
    invoice = _make_invoice(client, manager_headers, po, invoice_number="INV-PPT")
    _submit_invoice(client, manager_headers, invoice)
    _approve_invoice(client, admin_headers, invoice)

    over = client.post(
        "/api/v1/purchasing/payments",
        headers=manager_headers,
        json={
            "supplier_id": supplier["id"],
            "invoice_id": invoice["id"],
            "amount": 60.0,
            "payment_method": "cash",
        },
    )
    assert over.status_code == 400
    assert "exceeds outstanding" in over.json()["detail"]

    first = client.post(
        "/api/v1/purchasing/payments",
        headers=manager_headers,
        json={
            "supplier_id": supplier["id"],
            "invoice_id": invoice["id"],
            "amount": 20.0,
            "payment_method": "cash",
        },
    ).json()
    client.post(
        f"/api/v1/purchasing/payments/{first['id']}/submit-review",
        headers=manager_headers,
        json={},
    )
    client.post(
        f"/api/v1/purchasing/payments/{first['id']}/approve",
        headers=admin_headers,
        json={},
    )

    second = client.post(
        "/api/v1/purchasing/payments",
        headers=manager_headers,
        json={
            "supplier_id": supplier["id"],
            "invoice_id": invoice["id"],
            "amount": 30.0,
            "payment_method": "cash",
        },
    )
    assert second.status_code == 200, second.text
    client.post(
        f"/api/v1/purchasing/payments/{second.json()['id']}/submit-review",
        headers=manager_headers,
        json={},
    )
    client.post(
        f"/api/v1/purchasing/payments/{second.json()['id']}/approve",
        headers=admin_headers,
        json={},
    )

    remaining_over = client.post(
        "/api/v1/purchasing/payments",
        headers=manager_headers,
        json={
            "supplier_id": supplier["id"],
            "invoice_id": invoice["id"],
            "amount": 1.0,
            "payment_method": "cash",
        },
    )
    assert remaining_over.status_code == 400


def test_supplier_payment_requires_approved_invoice(
    client, manager_headers, admin_headers, make_product
):
    product = make_product(manager_headers, name="Pay Req", sku="SKU-PRQ", price=10.0)
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(client, manager_headers, supplier["id"], product["id"])
    _order_po(client, manager_headers, admin_headers, po)
    _receive_all(client, manager_headers, po)
    invoice = _make_invoice(client, manager_headers, po, invoice_number="INV-PRQ")

    resp = client.post(
        "/api/v1/purchasing/payments",
        headers=manager_headers,
        json={
            "supplier_id": supplier["id"],
            "invoice_id": invoice["id"],
            "amount": 10.0,
            "payment_method": "cash",
        },
    )
    assert resp.status_code == 400
    assert "approved" in resp.json()["detail"]


def test_supplier_payment_wrong_supplier_rejected(
    client, manager_headers, admin_headers, make_product
):
    product = make_product(manager_headers, name="Pay Sup", sku="SKU-PSU", price=10.0)
    supplier = _make_supplier(client, manager_headers)
    other = _make_supplier(client, manager_headers, name="Other Supplies")
    po = _make_po(client, manager_headers, supplier["id"], product["id"])
    _order_po(client, manager_headers, admin_headers, po)
    _receive_all(client, manager_headers, po)
    invoice = _make_invoice(client, manager_headers, po, invoice_number="INV-PSU")
    _submit_invoice(client, manager_headers, invoice)
    _approve_invoice(client, admin_headers, invoice)

    resp = client.post(
        "/api/v1/purchasing/payments",
        headers=manager_headers,
        json={
            "supplier_id": other["id"],
            "invoice_id": invoice["id"],
            "amount": 10.0,
            "payment_method": "cash",
        },
    )
    assert resp.status_code == 400
    assert "does not belong" in resp.json()["detail"]


def test_supplier_payment_self_approval_rejected(
    client, manager_headers, admin_headers, make_product
):
    product = make_product(manager_headers, name="Pay Self", sku="SKU-PSL", price=10.0)
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(client, manager_headers, supplier["id"], product["id"])
    _order_po(client, manager_headers, admin_headers, po)
    _receive_all(client, manager_headers, po)
    invoice = _make_invoice(client, manager_headers, po, invoice_number="INV-PSL")
    _submit_invoice(client, manager_headers, invoice)
    _approve_invoice(client, admin_headers, invoice)

    payment = client.post(
        "/api/v1/purchasing/payments",
        headers=admin_headers,
        json={
            "supplier_id": supplier["id"],
            "invoice_id": invoice["id"],
            "amount": 10.0,
            "payment_method": "cash",
        },
    ).json()
    client.post(
        f"/api/v1/purchasing/payments/{payment['id']}/submit-review",
        headers=admin_headers,
        json={},
    )

    resp = client.post(
        f"/api/v1/purchasing/payments/{payment['id']}/approve",
        headers=admin_headers,
        json={},
    )
    assert resp.status_code == 403
    assert "you created" in resp.json()["detail"]


def test_supplier_payment_reject_flow(
    client, manager_headers, admin_headers, make_product
):
    product = make_product(manager_headers, name="Pay Rej", sku="SKU-PRJ", price=10.0)
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(client, manager_headers, supplier["id"], product["id"])
    _order_po(client, manager_headers, admin_headers, po)
    _receive_all(client, manager_headers, po)
    invoice = _make_invoice(client, manager_headers, po, invoice_number="INV-PRJ")
    _submit_invoice(client, manager_headers, invoice)
    _approve_invoice(client, admin_headers, invoice)

    payment = client.post(
        "/api/v1/purchasing/payments",
        headers=manager_headers,
        json={
            "supplier_id": supplier["id"],
            "invoice_id": invoice["id"],
            "amount": 50.0,
            "payment_method": "cash",
        },
    ).json()
    client.post(
        f"/api/v1/purchasing/payments/{payment['id']}/submit-review",
        headers=manager_headers,
        json={},
    )

    rejected = client.post(
        f"/api/v1/purchasing/payments/{payment['id']}/reject",
        headers=admin_headers,
        json={"review_note": "wrong reference"},
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "rejected"

    summary = client.get(
        "/api/v1/reports/supplier-payments", headers=manager_headers
    ).json()
    assert summary["rejected_count"] == 1
    assert summary["approved_total"] == 0.0
    assert summary["outstanding_payable"] == 50.0


def test_purchasing_actions_are_audited(
    client, manager_headers, admin_headers, make_product, db
):
    product = make_product(manager_headers, name="Audit Me", sku="SKU-AUD", price=10.0)
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(client, manager_headers, supplier["id"], product["id"])
    _order_po(client, manager_headers, admin_headers, po)
    _receive_all(client, manager_headers, po)
    invoice = _make_invoice(client, manager_headers, po, invoice_number="INV-AUD")
    _submit_invoice(client, manager_headers, invoice)
    _approve_invoice(client, admin_headers, invoice)

    payment = client.post(
        "/api/v1/purchasing/payments",
        headers=manager_headers,
        json={
            "supplier_id": supplier["id"],
            "invoice_id": invoice["id"],
            "amount": 50.0,
            "payment_method": "cash",
        },
    ).json()
    client.post(
        f"/api/v1/purchasing/payments/{payment['id']}/submit-review",
        headers=manager_headers,
        json={},
    )
    client.post(
        f"/api/v1/purchasing/payments/{payment['id']}/approve",
        headers=admin_headers,
        json={},
    )

    from app.models.audit_log import AuditLog

    actions = [row.action for row in db.query(AuditLog).order_by(AuditLog.id).all()]
    for expected in (
        "purchase_order.create",
        "purchase_order.submit",
        "purchase_order.approve",
        "purchase_order.receive",
        "purchase_invoice.create",
        "purchase_invoice.submit",
        "purchase_invoice.approve",
        "supplier_payment.create",
        "supplier_payment.submit",
        "supplier_payment.approve",
    ):
        assert expected in actions, f"missing audit action {expected}"
