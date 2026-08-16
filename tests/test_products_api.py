"""Integration tests for the products API: delete guards, category delete,
and unit_cost (COGS) persistence."""

from conftest import order_payload


def _make_supplier(client, manager_headers):
    resp = client.post(
        "/api/v1/purchasing/suppliers",
        headers=manager_headers,
        json={"name": "Guard Supplies", "contact_email": "guard@acme.test"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _make_po(client, manager_headers, supplier_id, product_id):
    resp = client.post(
        "/api/v1/purchasing/orders",
        headers=manager_headers,
        json={
            "supplier_id": supplier_id,
            "items": [
                {
                    "product_id": product_id,
                    "quantity_ordered": 5,
                    "unit_cost": 4.0,
                }
            ],
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_delete_unreferenced_product_succeeds(client, manager_headers, make_product):
    product = make_product(
        manager_headers, name="Lonely", sku="SKU-LONE", price=5.0, stock=0
    )
    resp = client.delete(f"/api/v1/products/{product['id']}", headers=manager_headers)
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_delete_product_with_order_reference_rejected(
    client, manager_headers, cashier_headers, make_product, open_drawer
):
    product = make_product(
        manager_headers, name="Ordered", sku="SKU-ORD", price=10.0, stock=10
    )
    open_drawer(cashier_headers)
    order = client.post(
        "/api/v1/orders/",
        headers=cashier_headers,
        json=order_payload(product["id"], quantity=1),
    )
    assert order.status_code == 200, order.text

    resp = client.delete(f"/api/v1/products/{product['id']}", headers=manager_headers)
    assert resp.status_code == 400
    assert "order item" in resp.json()["detail"]


def test_delete_product_with_stock_movement_rejected(
    client, manager_headers, make_product
):
    product = make_product(
        manager_headers, name="Moved", sku="SKU-MOV", price=10.0, stock=5
    )
    resp = client.delete(f"/api/v1/products/{product['id']}", headers=manager_headers)
    assert resp.status_code == 400
    assert "stock movement" in resp.json()["detail"]


def test_delete_product_with_purchase_reference_rejected(
    client, manager_headers, make_product
):
    product = make_product(
        manager_headers, name="Procured", sku="SKU-PROC-G", price=10.0, stock=0
    )
    supplier = _make_supplier(client, manager_headers)
    po = _make_po(client, manager_headers, supplier["id"], product["id"])
    assert po["status"] == "draft"

    resp = client.delete(f"/api/v1/products/{product['id']}", headers=manager_headers)
    assert resp.status_code == 400
    assert "purchase order item" in resp.json()["detail"]


def test_delete_empty_category_succeeds(client, manager_headers):
    cat = client.post(
        "/api/v1/products/categories",
        headers=manager_headers,
        json={"name": "Empty Cat", "description": ""},
    ).json()
    resp = client.delete(
        f"/api/v1/products/categories/{cat['id']}", headers=manager_headers
    )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_delete_category_with_products_rejected(client, manager_headers, make_product):
    product = make_product(
        manager_headers, name="Cat Item", sku="SKU-CAT", price=5.0, stock=0
    )
    resp = client.delete(
        f"/api/v1/products/categories/{product['category']['id']}",
        headers=manager_headers,
    )
    assert resp.status_code == 400
    assert "product" in resp.json()["detail"]


def test_delete_missing_product_404(client, manager_headers):
    resp = client.delete("/api/v1/products/99999", headers=manager_headers)
    assert resp.status_code == 404


def test_product_unit_cost_create_and_update(client, manager_headers):
    cat = client.post(
        "/api/v1/products/categories",
        headers=manager_headers,
        json={"name": "Costly"},
    ).json()
    created = client.post(
        "/api/v1/products",
        headers=manager_headers,
        json={
            "name": "Cost Item",
            "sku": "SKU-COST",
            "price": 20.0,
            "unit_cost": 12.5,
            "stock_quantity": 0,
            "category_id": cat["id"],
        },
    )
    assert created.status_code == 200, created.text
    assert created.json()["unit_cost"] == 12.5

    updated = client.put(
        f"/api/v1/products/{created.json()['id']}",
        headers=manager_headers,
        json={"unit_cost": 11.0},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["unit_cost"] == 11.0


def test_upload_product_image(client, manager_headers, make_product):
    product = make_product(
        manager_headers, name="Photo Item", sku="PHOTO-1", price=5.0, stock=5
    )
    resp = client.post(
        f"/api/v1/products/{product['id']}/image",
        headers=manager_headers,
        files={"file": ("p.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 16, "image/png")},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["image_url"].startswith("/media/products/")
    assert resp.json()["image_url"].endswith(".png")

    # served via the static mount
    served = client.get(resp.json()["image_url"])
    assert served.status_code == 200


def test_upload_replaces_and_cleans_old_file(client, manager_headers, make_product):
    product = make_product(
        manager_headers, name="Photo Item 2", sku="PHOTO-2", price=5.0, stock=5
    )
    first = client.post(
        f"/api/v1/products/{product['id']}/image",
        headers=manager_headers,
        files={"file": ("a.png", b"first", "image/png")},
    ).json()
    second = client.post(
        f"/api/v1/products/{product['id']}/image",
        headers=manager_headers,
        files={"file": ("b.png", b"second", "image/png")},
    ).json()
    assert first["image_url"] != second["image_url"]
    # old file removed from disk
    assert client.get(first["image_url"]).status_code == 404


def test_upload_rejects_unsupported_type(client, manager_headers, make_product):
    product = make_product(
        manager_headers, name="Photo Item 3", sku="PHOTO-3", price=5.0, stock=5
    )
    resp = client.post(
        f"/api/v1/products/{product['id']}/image",
        headers=manager_headers,
        files={"file": ("evil.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 415


def test_upload_requires_manager(
    client, cashier_headers, manager_headers, make_product
):
    product = make_product(
        manager_headers, name="Photo Item 4", sku="PHOTO-4", price=5.0, stock=5
    )
    resp = client.post(
        f"/api/v1/products/{product['id']}/image",
        headers=cashier_headers,
        files={"file": ("p.png", b"x", "image/png")},
    )
    assert resp.status_code == 403


def test_delete_product_image(client, manager_headers, make_product):
    product = make_product(
        manager_headers, name="Photo Item 5", sku="PHOTO-5", price=5.0, stock=5
    )
    client.post(
        f"/api/v1/products/{product['id']}/image",
        headers=manager_headers,
        files={"file": ("p.png", b"x", "image/png")},
    )
    resp = client.delete(
        f"/api/v1/products/{product['id']}/image", headers=manager_headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["image_url"] is None


def test_category_color_validation(client, manager_headers):
    ok = client.post(
        "/api/v1/products/categories",
        headers=manager_headers,
        json={"name": "Colored", "color": "#E8F5E9"},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["color"] == "#E8F5E9"

    bad = client.post(
        "/api/v1/products/categories",
        headers=manager_headers,
        json={"name": "Bad", "color": "green"},
    )
    assert bad.status_code == 422


def test_update_category_color(client, manager_headers):
    created = client.post(
        "/api/v1/products/categories",
        headers=manager_headers,
        json={"name": "Editable", "color": "#E8F5E9"},
    ).json()
    updated = client.put(
        f"/api/v1/products/categories/{created['id']}",
        headers=manager_headers,
        json={"color": "#FFF3E0"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["color"] == "#FFF3E0"

    cleared = client.put(
        f"/api/v1/products/categories/{created['id']}",
        headers=manager_headers,
        json={"color": None},
    )
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["color"] is None

    bad = client.put(
        f"/api/v1/products/categories/{created['id']}",
        headers=manager_headers,
        json={"color": "blue"},
    )
    assert bad.status_code == 422


def test_category_color_palette_endpoint(client, cashier_headers):
    from app.admin.color_field import CATEGORY_COLOR_PALETTE

    resp = client.get("/api/v1/products/categories/colors", headers=cashier_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json() == CATEGORY_COLOR_PALETTE
    assert len(resp.json()) >= 8

    anonymous = client.get("/api/v1/products/categories/colors")
    assert anonymous.status_code == 401 or anonymous.status_code == 403
