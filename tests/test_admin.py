"""Integration tests for the sqladmin app: auth, dashboard, and reports."""

from app.core.config import settings


def _login(client, username=None, password=None):
    return client.post(
        "/admin/login",
        data={
            "username": username or settings.ADMIN_USERNAME,
            "password": password or settings.ADMIN_PASSWORD,
        },
        follow_redirects=False,
    )


def _make_superuser(db, user_id):
    from app.models.user import User

    user = db.get(User, user_id)
    user.is_superuser = True
    db.commit()
    return user


def test_admin_requires_login(client):
    resp = client.get("/admin/", follow_redirects=False)
    assert resp.status_code in (302, 303)
    assert "/admin/login" in resp.headers["location"]


def test_admin_login_success_redirects(client):
    resp = _login(client)
    assert resp.status_code in (302, 303)
    assert "/admin" in resp.headers["location"]


def test_admin_login_wrong_password_rejected(client):
    resp = _login(client, password="wrong-password")
    assert resp.status_code == 400
    assert "/admin/login" in str(resp.url)


def test_admin_dashboard_renders_after_login(client):
    login = _login(client)
    assert login.status_code in (302, 303)
    resp = client.get("/admin/")
    assert resp.status_code == 200


def test_admin_reports_page_renders(client):
    _login(client)
    resp = client.get("/admin/reports")
    assert resp.status_code == 200
    assert "Reports Dashboard" in resp.text
    assert "Executive Summary" in resp.text


def test_admin_logout_clears_session(client):
    _login(client)
    resp = client.get("/admin/logout", follow_redirects=False)
    assert resp.status_code in (302, 303)
    after = client.get("/admin/", follow_redirects=False)
    assert after.status_code in (302, 303)
    assert "/admin/login" in after.headers["location"]


def test_admin_login_rejects_regular_user(client, auth_factory, db):
    user = auth_factory.register("cashier_admin@example.com")
    assert user["is_superuser"] is False
    resp = _login(client, username="cashier_admin@example.com", password="TestPass123")
    assert resp.status_code == 400
    assert "/admin/login" in str(resp.url)


def test_admin_login_accepts_superuser(client, auth_factory, db):
    user = auth_factory.register("boss@example.com")
    _make_superuser(db, user["id"])
    login = _login(client, username="boss@example.com", password="TestPass123")
    assert login.status_code in (302, 303)
    assert "/admin" in login.headers["location"]
    resp = client.get("/admin/")
    assert resp.status_code == 200


def test_admin_login_rejects_inactive_superuser(client, auth_factory, db):
    user = auth_factory.register("exboss@example.com")
    _make_superuser(db, user["id"])
    from app.models.user import User

    boss = db.get(User, user["id"])
    boss.is_active = False
    db.commit()
    resp = _login(client, username="exboss@example.com", password="TestPass123")
    assert resp.status_code == 400
    assert "/admin/login" in str(resp.url)


def test_system_role_cannot_be_deleted(client, db):
    from app.models.rbac import Role

    role = db.query(Role).filter(Role.is_system.is_(True)).first()
    assert role is not None
    _login(client)
    resp = client.delete(f"/admin/role/delete?pks={role.id}")
    assert resp.status_code == 403
    assert db.query(Role).filter(Role.id == role.id).one()


def test_user_role_can_be_deleted(client, db, auth_factory):
    from app.models.rbac import Role

    user = auth_factory.register("role-admin@example.com")
    _make_superuser(db, user["id"])
    new_role = Role(name="temp-role", description="disposable", is_system=False)
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    _login(client, username="role-admin@example.com", password="TestPass123")
    resp = client.delete(f"/admin/role/delete?pks={new_role.id}")
    assert resp.status_code == 200
    assert db.query(Role).filter(Role.id == new_role.id).count() == 0


def test_adjust_stock_writes_movement(client, auth_factory, db):
    from app.models.product import Product
    from app.models.stock_movement import StockMovement

    user = auth_factory.register("stock-admin@example.com")
    _make_superuser(db, user["id"])
    _login(client, username="stock-admin@example.com", password="TestPass123")

    resp = client.get("/admin/product/adjust-stock?pk=999999")
    assert resp.status_code == 404

    product = Product(
        name="Adjustable Widget",
        sku="SKU-ADJ-1",
        price=10.0,
        stock_quantity=5,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    page = client.get(f"/admin/product/adjust-stock?pk={product.id}")
    assert page.status_code == 200
    assert "Adjust Stock" in page.text
    assert "Current stock" in page.text

    resp = client.post(
        f"/admin/product/adjust-stock?pk={product.id}",
        data={"delta": "25", "note": "cycle count correction"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    db.expire_all()
    assert db.get(Product, product.id).stock_quantity == 30
    movement = (
        db.query(StockMovement).filter(StockMovement.product_id == product.id).one()
    )
    assert movement.movement_type == "manual_adjustment"
    assert movement.quantity_before == 5
    assert movement.quantity_delta == 25
    assert movement.quantity_after == 30


def test_adjust_stock_rejects_negative_result(client, auth_factory, db):
    from app.models.product import Product

    user = auth_factory.register("stock-admin2@example.com")
    _make_superuser(db, user["id"])
    _login(client, username="stock-admin2@example.com", password="TestPass123")

    product = Product(
        name="Low Widget",
        sku="SKU-ADJ-2",
        price=10.0,
        stock_quantity=2,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    resp = client.post(
        f"/admin/product/adjust-stock?pk={product.id}",
        data={"delta": "-99", "note": "shrinkage"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    db.expire_all()
    assert db.get(Product, product.id).stock_quantity == 2


def test_admin_product_list_renders_category_label(client, auth_factory, assign_role):
    """Relationship columns show labels (category name) not object reprs."""
    user = auth_factory.register("label-manager@example.com")
    assign_role(user["id"], "manager")
    headers = auth_factory.login("label-manager@example.com")
    cat_resp = client.post(
        "/api/v1/products/categories",
        headers=headers,
        json={"name": "Fancy Category", "description": "x"},
    )
    assert cat_resp.status_code == 200, cat_resp.text
    resp = client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "name": "Labeled Widget",
            "sku": "SKU-LBL-1",
            "price": 9.99,
            "stock_quantity": 5,
            "category_id": cat_resp.json()["id"],
        },
    )
    assert resp.status_code == 200, resp.text

    _login(client)
    page = client.get("/admin/product/list")
    assert page.status_code == 200
    assert "Fancy Category" in page.text
    assert "<Category" not in page.text


def test_admin_role_detail_renders_permission_codes(client, db):
    """To-many relationship columns join labels (permission codes).

    sqladmin renders to-many relationship columns only in the detail view;
    the LabeledRelationsMixin formats them as permission codes there.
    """
    _login(client)
    page = client.get("/admin/role/list")
    assert page.status_code == 200
    assert "cashier" in page.text

    page = client.get("/admin/role/details/1")
    assert page.status_code == 200
    assert "orders:manage" in page.text
    assert "<Permission" not in page.text


def test_admin_stock_movement_list_renders_product_and_user(
    client, auth_factory, assign_role
):
    """Both scalar- and to-many relation columns render labels in one row."""
    user = auth_factory.register("label-mgr2@example.com")
    assign_role(user["id"], "manager")
    headers = auth_factory.login("label-mgr2@example.com")
    cat_resp = client.post(
        "/api/v1/products/categories",
        headers=headers,
        json={"name": "Cat B", "description": "x"},
    )
    resp = client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "name": "Movement Widget",
            "sku": "SKU-MOV-1",
            "price": 5.0,
            "stock_quantity": 8,
            "category_id": cat_resp.json()["id"],
        },
    )
    assert resp.status_code == 200, resp.text

    _login(client)
    page = client.get("/admin/stock-movement/list")
    assert page.status_code == 200
    assert "Movement Widget" in page.text
    assert "label-mgr2@example.com" in page.text
    assert "<Product" not in page.text
    assert "<User" not in page.text


def test_admin_product_create_form_renders_category_label(
    client, auth_factory, assign_role
):
    """Create form dropdowns show relation labels (category name) not object reprs."""
    user = auth_factory.register("form-label-mgr@example.com")
    assign_role(user["id"], "manager")
    headers = auth_factory.login("form-label-mgr@example.com")
    cat_resp = client.post(
        "/api/v1/products/categories",
        headers=headers,
        json={"name": "Form Fancy Category", "description": "x"},
    )
    assert cat_resp.status_code == 200, cat_resp.text

    _login(client)
    page = client.get("/admin/product/create")
    assert page.status_code == 200
    assert "Form Fancy Category" in page.text
    assert "<Category" not in page.text


def test_admin_product_edit_form_renders_category_label(
    client, db, auth_factory, assign_role
):
    """Edit form pre-selects the relation with a label, not an object repr."""
    from app.models.product import Category, Product

    user = auth_factory.register("edit-form-label@example.com")
    assign_role(user["id"], "manager")
    headers = auth_factory.login("edit-form-label@example.com")
    cat_resp = client.post(
        "/api/v1/products/categories",
        headers=headers,
        json={"name": "Edit Fancy Category", "description": "x"},
    )
    assert cat_resp.status_code == 200, cat_resp.text
    category_id = cat_resp.json()["id"]
    product = Product(
        name="Edit Form Widget",
        sku="SKU-EDIT-FORM-1",
        price=3.5,
        stock_quantity=2,
        category_id=category_id,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    _login(client)
    page = client.get(f"/admin/product/edit/{product.id}")
    assert page.status_code == 200
    assert "Edit Fancy Category" in page.text
    assert "<Category" not in page.text


def test_admin_role_edit_form_renders_permission_codes(client, db):
    """To-many relationship selects show labels (permission codes) in forms."""
    from app.models.rbac import Permission, Role

    _login(client)
    role = Role(name="form-label-role", description="editable", is_system=False)
    perm = db.query(Permission).filter(Permission.code == "orders:manage").one()
    role.permissions.append(perm)
    db.add(role)
    db.commit()
    db.refresh(role)

    page = client.get(f"/admin/role/edit/{role.id}")
    assert page.status_code == 200
    assert "orders:manage" in page.text
    assert "<Permission" not in page.text


def test_admin_detail_pages_render_relation_labels(client, db, auth_factory):
    """Detail pages label every relationship, never rendering object reprs.

    sqladmin renders all model attributes on the detail page by default, so
    relationships outside ``column_list`` must still be formatted.
    """
    from decimal import Decimal

    from app.models.customer import Customer
    from app.models.drawer import DrawerSession
    from app.models.order import Order, OrderItem
    from app.models.payment import Payment
    from app.models.product import Category, Product
    from app.models.promotion import Promotion
    from app.models.purchase import (PurchaseInvoice, PurchaseInvoiceItem,
                                     PurchaseOrder, PurchaseOrderItem,
                                     Supplier)
    from app.models.refund import Refund, RefundItem
    from app.models.stock_movement import StockMovement
    from app.models.tax import OrderTaxLine, TaxRule

    boss = auth_factory.register("detail-boss@example.com")
    _make_superuser(db, boss["id"])
    _login(client, username="detail-boss@example.com", password="TestPass123")
    user_id = boss["id"]

    category = Category(name="Detail Cat", description="x")
    product = Product(
        name="Detail Widget",
        sku="SKU-DTL-1",
        price=7.0,
        stock_quantity=10,
        category=category,
    )
    supplier = Supplier(name="Detail Supplier")
    customer = Customer(name="Detail Customer")
    promotion = Promotion(
        code="DTL10",
        name="Detail Promo",
        discount_type="percentage",
        discount_value=10,
    )
    tax_rule = TaxRule(name="Detail VAT", rate=Decimal("0.11"))
    db.add_all([category, product, supplier, customer, promotion, tax_rule])
    db.flush()

    po = PurchaseOrder(supplier_id=supplier.id, user_id=user_id)
    db.add(po)
    db.flush()
    po_item = PurchaseOrderItem(
        purchase_order_id=po.id,
        product_id=product.id,
        quantity_ordered=5,
        unit_cost=Decimal("2.00"),
    )
    db.add(po_item)
    db.flush()
    invoice = PurchaseInvoice(
        supplier_id=supplier.id,
        purchase_order_id=po.id,
        user_id=user_id,
        invoice_number="INV-DTL-1",
    )
    db.add(invoice)
    db.flush()
    invoice_item = PurchaseInvoiceItem(
        invoice_id=invoice.id,
        purchase_order_item_id=po_item.id,
        product_id=product.id,
        billed_quantity=5,
        billed_unit_cost=Decimal("2.00"),
        expected_quantity=5,
        expected_unit_cost=Decimal("2.00"),
    )
    db.add(invoice_item)

    drawer = DrawerSession(user_id=user_id)
    db.add(drawer)
    db.flush()
    order = Order(user_id=user_id, customer_id=customer.id, drawer_session_id=drawer.id)
    db.add(order)
    db.flush()
    order_item = OrderItem(
        order_id=order.id, product_id=product.id, quantity=2, unit_price=Decimal("7.00")
    )
    tax_line = OrderTaxLine(
        order_id=order.id,
        tax_rule_id=tax_rule.id,
        tax_name="VAT",
        tax_scope="order",
        tax_mode="exclusive",
        tax_rate=Decimal("0.11"),
        taxable_base=Decimal("14.00"),
        tax_amount=Decimal("1.54"),
    )
    payment = Payment(
        order_id=order.id,
        user_id=user_id,
        payment_method="cash",
        amount=Decimal("14.00"),
    )
    refund = Refund(order_id=order.id, user_id=user_id)
    db.add_all([order_item, tax_line, payment, refund])
    db.flush()
    refund_item = RefundItem(
        refund_id=refund.id,
        order_item_id=order_item.id,
        product_id=product.id,
        quantity=1,
        unit_price=Decimal("7.00"),
    )
    db.add(refund_item)
    db.flush()
    movement = StockMovement(
        product_id=product.id,
        user_id=user_id,
        order_id=order.id,
        order_item_id=order_item.id,
        purchase_order_id=po.id,
        purchase_order_item_id=po_item.id,
        refund_id=refund.id,
        movement_type="purchase",
        quantity_before=5,
        quantity_delta=5,
        quantity_after=10,
    )
    db.add(movement)
    db.commit()

    detail_urls = [
        f"/admin/category/details/{category.id}",
        f"/admin/product/details/{product.id}",
        f"/admin/promotion/details/{promotion.id}",
        f"/admin/customer/details/{customer.id}",
        f"/admin/supplier/details/{supplier.id}",
        f"/admin/purchase-order/details/{po.id}",
        f"/admin/purchase-order-item/details/{po_item.id}",
        f"/admin/purchase-invoice/details/{invoice.id}",
        f"/admin/purchase-invoice-item/details/{invoice_item.id}",
        f"/admin/order/details/{order.id}",
        f"/admin/order-item/details/{order_item.id}",
        f"/admin/order-tax-line/details/{tax_line.id}",
        f"/admin/drawer-session/details/{drawer.id}",
        f"/admin/refund/details/{refund.id}",
        f"/admin/refund-item/details/{refund_item.id}",
        f"/admin/stock-movement/details/{movement.id}",
    ]
    for url in detail_urls:
        resp = client.get(url)
        assert resp.status_code == 200, f"{url}: {resp.status_code}"
        assert "object at 0x" not in resp.text, f"raw repr on {url}"

    page = client.get(f"/admin/stock-movement/details/{movement.id}")
    assert f"Order #{order.id}" in page.text
    assert f"PO #{po.id}" in page.text
    assert f"PO Item #{po_item.id}" in page.text
    assert f"Refund #{refund.id}" in page.text

    page = client.get(f"/admin/order-item/details/{order_item.id}")
    assert f"Order #{order.id}" in page.text
    assert f"Refund Item #{refund_item.id}" in page.text

    page = client.get(f"/admin/purchase-invoice/details/{invoice.id}")
    assert f"Invoice Item #{invoice_item.id}" in page.text
    assert "INV-DTL-1" in page.text

    page = client.get(f"/admin/drawer-session/details/{drawer.id}")
    assert f"Order #{order.id}" in page.text

    page = client.get(f"/admin/category/details/{category.id}")
    assert "Detail Widget" in page.text


def test_admin_drawer_session_list_and_filter_render(client, db, auth_factory):
    """Drawer session filters use ColumnFilter instances (no 500)."""
    from app.models.drawer import DrawerSession

    boss = auth_factory.register("drawer-boss@example.com")
    _make_superuser(db, boss["id"])
    _login(client, username="drawer-boss@example.com", password="TestPass123")
    drawer = DrawerSession(user_id=boss["id"])
    db.add(drawer)
    db.commit()

    resp = client.get("/admin/drawer-session/list")
    assert resp.status_code == 200
    assert "drawer-boss@example.com" in resp.text

    resp = client.get("/admin/drawer-session/list?status=open")
    assert resp.status_code == 200
    assert "drawer-boss@example.com" in resp.text
