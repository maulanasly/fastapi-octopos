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


def test_admin_reports_page_renders(client, db):
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
        tenant_id=1,
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
        tenant_id=1,
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
    from app.models.product import Product

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
        tenant_id=1,
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
    from app.models.purchase import (
        PurchaseInvoice,
        PurchaseInvoiceItem,
        PurchaseOrder,
        PurchaseOrderItem,
        Supplier,
    )
    from app.models.refund import Refund, RefundItem
    from app.models.stock_movement import StockMovement
    from app.models.tax import OrderTaxLine, TaxRule

    boss = auth_factory.register("detail-boss@example.com")
    _make_superuser(db, boss["id"])
    _login(client, username="detail-boss@example.com", password="TestPass123")
    user_id = boss["id"]

    category = Category(name="Detail Cat", description="x", tenant_id=1)
    product = Product(
        name="Detail Widget",
        sku="SKU-DTL-1",
        price=7.0,
        stock_quantity=10,
        category=category,
        tenant_id=1,
    )
    supplier = Supplier(name="Detail Supplier", tenant_id=1)
    customer = Customer(name="Detail Customer", tenant_id=1)
    promotion = Promotion(
        code="DTL10",
        name="Detail Promo",
        discount_type="percentage",
        discount_value=10,
        tenant_id=1,
    )
    tax_rule = TaxRule(name="Detail VAT", rate=Decimal("0.11"), tenant_id=1)
    db.add_all([category, product, supplier, customer, promotion, tax_rule])
    db.flush()

    po = PurchaseOrder(supplier_id=supplier.id, user_id=user_id, tenant_id=1)
    db.add(po)
    db.flush()
    po_item = PurchaseOrderItem(
        purchase_order_id=po.id,
        product_id=product.id,
        quantity_ordered=5,
        unit_cost=Decimal("2.00"),
        tenant_id=1,
    )
    db.add(po_item)
    db.flush()
    invoice = PurchaseInvoice(
        supplier_id=supplier.id,
        purchase_order_id=po.id,
        user_id=user_id,
        invoice_number="INV-DTL-1",
        tenant_id=1,
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
        tenant_id=1,
    )
    db.add(invoice_item)

    drawer = DrawerSession(user_id=user_id, tenant_id=1)
    db.add(drawer)
    db.flush()
    order = Order(
        user_id=user_id,
        customer_id=customer.id,
        drawer_session_id=drawer.id,
        tenant_id=1,
    )
    db.add(order)
    db.flush()
    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=2,
        unit_price=Decimal("7.00"),
        tenant_id=1,
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
        tenant_id=1,
    )
    payment = Payment(
        order_id=order.id,
        user_id=user_id,
        payment_method="cash",
        amount=Decimal("14.00"),
        tenant_id=1,
    )
    refund = Refund(order_id=order.id, user_id=user_id, tenant_id=1)
    db.add_all([order_item, tax_line, payment, refund])
    db.flush()
    refund_item = RefundItem(
        refund_id=refund.id,
        order_item_id=order_item.id,
        product_id=product.id,
        quantity=1,
        unit_price=Decimal("7.00"),
        tenant_id=1,
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
        tenant_id=1,
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
    drawer = DrawerSession(user_id=boss["id"], tenant_id=1)
    db.add(drawer)
    db.commit()

    resp = client.get("/admin/drawer-session/list")
    assert resp.status_code == 200
    assert "drawer-boss@example.com" in resp.text

    resp = client.get("/admin/drawer-session/list?status=open")
    assert resp.status_code == 200
    assert "drawer-boss@example.com" in resp.text


def _workflow_admin(client, auth_factory, db, email):
    user = auth_factory.register(email)
    _make_superuser(db, user["id"])
    _login(client, username=email, password="TestPass123")
    return user["id"]


def _seed_low_stock(db, supplier_name="Workflow Supplier"):
    from decimal import Decimal

    from app.models.product import Category, Product
    from app.models.purchase import Supplier

    supplier = Supplier(name=supplier_name, tenant_id=1)
    category = Category(name="Workflow Cat", description="x", tenant_id=1)
    product = Product(
        name="Workflow Widget",
        sku="SKU-WF-1",
        price=10.0,
        unit_cost=Decimal("4.00"),
        stock_quantity=2,
        min_stock=1,
        max_stock=20,
        reorder_point=5,
        lead_time_days=3,
        category=category,
        tenant_id=1,
    )
    db.add_all([supplier, category, product])
    db.commit()
    db.refresh(product)
    return supplier, product


def test_workflows_hub_renders(client, auth_factory, db):
    _workflow_admin(client, auth_factory, db, "workflow-boss@example.com")
    resp = client.get("/admin/workflows")
    assert resp.status_code == 200
    assert "Restock" in resp.text
    assert "Invoicing" in resp.text
    assert "Close Drawer" in resp.text
    assert "Refund" in resp.text


def test_menu_sidebar_renders_categories(client, auth_factory, db):
    """Sidebar groups views under workflow categories."""
    _workflow_admin(client, auth_factory, db, "menu-boss@example.com")
    resp = client.get("/admin/")
    assert resp.status_code == 200
    for label in (
        "Workflows",
        "Sales",
        "Purchasing",
        "Inventory",
        "Customers",
        "Access Control",
        "Operations",
        "System",
        "Reports",
    ):
        assert label in resp.text


def test_restock_workflow_generates_and_receives(client, auth_factory, db):
    from decimal import Decimal

    from app.models.product import Product
    from app.models.purchase import PurchaseOrder, PurchaseOrderItem
    from app.models.stock_movement import StockMovement

    user_id = _workflow_admin(client, auth_factory, db, "restock-boss@example.com")
    supplier, product = _seed_low_stock(db)
    # Give the product supplier history so the auto-PO picks it. The history
    # PO must not be pending, otherwise the product is skipped.
    po = PurchaseOrder(
        supplier_id=supplier.id, user_id=user_id, status="received", tenant_id=1
    )
    db.add(po)
    db.flush()
    db.add(
        PurchaseOrderItem(
            purchase_order_id=po.id,
            product_id=product.id,
            quantity_ordered=1,
            quantity_received=1,
            unit_cost=Decimal("4.00"),
            tenant_id=1,
        )
    )
    db.commit()

    page = client.get("/admin/workflows/restock")
    assert page.status_code == 200
    assert "Workflow Widget" in page.text

    resp = client.post(
        "/admin/workflows/restock",
        data={"step": "generate", "lookback_days": "30"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "step=receive" in resp.headers["location"]

    new_po = (
        db.query(PurchaseOrder)
        .filter(PurchaseOrder.id != po.id)
        .order_by(PurchaseOrder.id.desc())
        .first()
    )
    assert new_po is not None
    assert new_po.status == "draft"

    page = client.get(f"/admin/workflows/restock?step=receive&po_id={new_po.id}")
    assert page.status_code == 200
    assert f"PO #{new_po.id}" in page.text

    po_item = new_po.items[0]
    resp = client.post(
        "/admin/workflows/restock",
        data={
            "step": "receive",
            "po_id": str(new_po.id),
            f"qty_{po_item.id}": str(po_item.quantity_ordered),
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "step=done" in resp.headers["location"]

    db.expire_all()
    assert db.get(Product, product.id).stock_quantity == 2 + po_item.quantity_ordered
    new_po = db.get(PurchaseOrder, new_po.id)
    assert new_po.status == "received"
    movement = (
        db.query(StockMovement)
        .filter(StockMovement.purchase_order_id == new_po.id)
        .one()
    )
    assert movement.quantity_before == 2
    assert movement.quantity_delta == po_item.quantity_ordered
    assert movement.quantity_after == 2 + po_item.quantity_ordered


def test_restock_workflow_generate_empty_when_healthy(client, auth_factory, db):
    _workflow_admin(client, auth_factory, db, "restock2-boss@example.com")
    resp = client.post(
        "/admin/workflows/restock",
        data={"step": "generate", "lookback_days": "30"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    page = client.get("/admin/workflows/restock?step=receive")
    assert page.status_code == 200
    assert "No draft purchase orders to receive" in page.text


def test_restock_workflow_manual_create_po(client, auth_factory, db):
    from decimal import Decimal

    from app.models.purchase import PurchaseOrder

    user_id = _workflow_admin(client, auth_factory, db, "manual-po-boss@example.com")
    supplier, product = _seed_low_stock(db)

    resp = client.post(
        "/admin/workflows/restock",
        data={
            "step": "create",
            "supplier_id": str(supplier.id),
            "notes": "manual order",
            f"qty_{product.id}": "7",
            f"cost_{product.id}": "4.50",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "step=receive" in resp.headers["location"]

    po = db.query(PurchaseOrder).order_by(PurchaseOrder.id.desc()).first()
    assert po is not None
    assert po.supplier_id == supplier.id
    assert po.user_id == user_id
    assert po.status == "draft"
    assert po.tenant_id == 1
    assert po.notes == "manual order"
    assert len(po.items) == 1
    item = po.items[0]
    assert item.product_id == product.id
    assert item.quantity_ordered == 7
    assert item.quantity_received == 0
    assert item.unit_cost == Decimal("4.50")
    assert po.total_estimated_amount == Decimal("31.50")


def test_restock_workflow_mark_ordered(client, auth_factory, db):
    from decimal import Decimal

    from app.models.purchase import PurchaseOrder, PurchaseOrderItem

    user_id = _workflow_admin(client, auth_factory, db, "order-po-boss@example.com")
    supplier, product = _seed_low_stock(db)
    po = PurchaseOrder(
        supplier_id=supplier.id, user_id=user_id, status="draft", tenant_id=1
    )
    db.add(po)
    db.flush()
    db.add(
        PurchaseOrderItem(
            purchase_order_id=po.id,
            product_id=product.id,
            quantity_ordered=3,
            quantity_received=0,
            unit_cost=Decimal("4.00"),
            tenant_id=1,
        )
    )
    db.commit()
    po_id = po.id

    resp = client.post(
        "/admin/workflows/restock",
        data={"step": "order", "po_id": str(po_id)},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    db.expire_all()
    marked = db.get(PurchaseOrder, po_id)
    assert marked.status == "ordered"
    assert marked.ordered_at is not None


def test_restock_workflow_manual_create_rejects_no_supplier(client, auth_factory, db):
    _workflow_admin(client, auth_factory, db, "bad-po-boss@example.com")
    _, product = _seed_low_stock(db)

    resp = client.post(
        "/admin/workflows/restock",
        data={"step": "create", f"qty_{product.id}": "2", f"cost_{product.id}": "1"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "step=create" in resp.headers["location"]


def test_restock_workflow_manual_create_rejects_no_items(client, auth_factory, db):
    _workflow_admin(client, auth_factory, db, "noitem-po-boss@example.com")
    supplier, _ = _seed_low_stock(db)

    resp = client.post(
        "/admin/workflows/restock",
        data={"step": "create", "supplier_id": str(supplier.id)},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "step=create" in resp.headers["location"]


def test_restock_workflow_scoped_to_admin_tenant(client, auth_factory, db):
    """Products/POs from other tenants are not offered to the admin workflow."""
    from app.models.tenant import Tenant

    _workflow_admin(client, auth_factory, db, "scoped-po-boss@example.com")
    supplier, product = _seed_low_stock(db, supplier_name="Other Tenant Supplier")
    tenant2 = Tenant(name="Other Tenant", slug="other-tenant")
    db.add(tenant2)
    db.commit()
    db.refresh(tenant2)
    product.tenant_id = tenant2.id
    product.category.tenant_id = tenant2.id
    supplier.tenant_id = tenant2.id
    db.commit()

    page = client.get("/admin/workflows/restock?step=create")
    assert page.status_code == 200
    assert "Other Tenant Supplier" not in page.text
    assert "Workflow Widget" not in page.text

    page = client.get("/admin/workflows/restock")
    assert page.status_code == 200
    assert "Workflow Widget" not in page.text


def test_invoice_workflow_creates_and_approves(client, auth_factory, db):
    """Create an invoice from a received PO, then approve it."""
    from decimal import Decimal

    from app.models.purchase import PurchaseInvoice, PurchaseOrder, PurchaseOrderItem

    user_id = _workflow_admin(client, auth_factory, db, "invoice-boss@example.com")
    supplier, product = _seed_low_stock(db)
    po = PurchaseOrder(supplier_id=supplier.id, user_id=user_id, tenant_id=1)
    db.add(po)
    db.flush()
    po_item = PurchaseOrderItem(
        purchase_order_id=po.id,
        product_id=product.id,
        quantity_ordered=10,
        quantity_received=10,
        unit_cost=Decimal("4.00"),
        tenant_id=1,
    )
    db.add(po_item)
    db.commit()

    resp = client.post(
        "/admin/workflows/invoice",
        data={"step": "select", "po_id": str(po.id)},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "step=create" in resp.headers["location"]

    page = client.get(f"/admin/workflows/invoice?step=create&po_id={po.id}")
    assert page.status_code == 200
    assert "Workflow Widget" in page.text

    resp = client.post(
        f"/admin/workflows/invoice?step=create&po_id={po.id}",
        data={
            "step": "create",
            "invoice_number": "INV-WF-001",
            f"bill_qty_{po_item.id}": "10",
            f"bill_cost_{po_item.id}": "4.00",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    invoice_id = int(resp.headers["location"].split("invoice_id=")[1])
    invoice = db.get(PurchaseInvoice, invoice_id)
    assert invoice is not None
    assert invoice.status == "draft"
    assert invoice.total_amount == 40

    page = client.get(f"/admin/workflows/invoice?step=review&invoice_id={invoice_id}")
    assert page.status_code == 200
    assert "INV-WF-001" in page.text

    resp = client.post(
        f"/admin/workflows/invoice?step=review&invoice_id={invoice_id}",
        data={"step": "review", "action": "submit", "review_note": "ready"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    db.expire_all()
    assert db.get(PurchaseInvoice, invoice_id).status == "pending_review"

    page = client.get(f"/admin/workflows/invoice?step=review&invoice_id={invoice_id}")
    assert "Approve" in page.text

    resp = client.post(
        f"/admin/workflows/invoice?step=review&invoice_id={invoice_id}",
        data={"step": "review", "action": "approve", "review_note": "looks good"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    db.expire_all()
    assert db.get(PurchaseInvoice, invoice_id).status == "approved"


def test_close_drawer_workflow_reconciles(client, auth_factory, db):
    """Close an open drawer with counted cash; reconciliation recorded."""
    from app.models.drawer import DrawerSession
    from app.models.shift_reconciliation import ShiftReconciliation

    user_id = _workflow_admin(client, auth_factory, db, "drawer2-boss@example.com")
    drawer = DrawerSession(user_id=user_id, starting_cash=100.0, tenant_id=1)
    db.add(drawer)
    db.commit()

    resp = client.post(
        "/admin/workflows/close-drawer",
        data={"step": "select", "drawer_id": str(drawer.id)},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "step=count" in resp.headers["location"]

    page = client.get(f"/admin/workflows/close-drawer?step=count&drawer_id={drawer.id}")
    assert page.status_code == 200
    assert "Expected cash" in page.text

    resp = client.post(
        f"/admin/workflows/close-drawer?step=count&drawer_id={drawer.id}",
        data={
            "step": "count",
            "counted_cash": "95.5",
            "counted_non_cash": "0",
            "notes": "end of day",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    db.expire_all()
    drawer = db.get(DrawerSession, drawer.id)
    assert drawer.status == "closed"
    assert drawer.ending_cash == 95.5
    recon = (
        db.query(ShiftReconciliation)
        .filter(ShiftReconciliation.drawer_session_id == drawer.id)
        .one()
    )
    assert recon.cash_variance == -4.5
    assert recon.closed_by_user_id == user_id


def test_refund_workflow_records_refund(client, auth_factory, db):
    """Refund items from a completed order; stock restored."""
    from decimal import Decimal

    from app.models.customer import Customer
    from app.models.order import Order, OrderItem
    from app.models.product import Product
    from app.models.refund import Refund
    from app.models.stock_movement import StockMovement

    supplier, product = _seed_low_stock(db)
    product.stock_quantity = 20
    db.commit()

    user_id = _workflow_admin(client, auth_factory, db, "refund-boss@example.com")
    customer = Customer(name="Refund Customer", tenant_id=1)
    db.add(customer)
    db.flush()
    order = Order(
        user_id=user_id, customer_id=customer.id, status="completed", tenant_id=1
    )
    db.add(order)
    db.flush()
    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=3,
        unit_price=Decimal("10.00"),
        tenant_id=1,
    )
    db.add(order_item)
    db.commit()

    resp = client.post(
        "/admin/workflows/refund",
        data={"step": "select", "order_id": str(order.id)},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "step=items" in resp.headers["location"]

    page = client.get(f"/admin/workflows/refund?step=items&order_id={order.id}")
    assert page.status_code == 200
    assert "Workflow Widget" in page.text

    resp = client.post(
        f"/admin/workflows/refund?step=items&order_id={order.id}",
        data={
            "step": "items",
            "reason": "damaged",
            "payment_method": "cash",
            f"refund_qty_{order_item.id}": "1",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "step=done" in resp.headers["location"]

    db.expire_all()
    refund = (
        db.query(Refund)
        .filter(Refund.order_id == order.id)
        .order_by(Refund.id.desc())
        .first()
    )
    assert refund is not None
    assert refund.items[0].quantity == 1
    assert db.get(Product, product.id).stock_quantity == 21
    movement = (
        db.query(StockMovement).filter(StockMovement.refund_id == refund.id).one()
    )
    assert movement.quantity_delta == 1


def test_refund_workflow_rejects_over_refund(client, auth_factory, db):
    """Refunding more than ordered is rejected with a flash and no record."""
    from decimal import Decimal

    from app.models.customer import Customer
    from app.models.order import Order, OrderItem
    from app.models.refund import Refund

    supplier, product = _seed_low_stock(db)
    product.stock_quantity = 20
    db.commit()

    user_id = _workflow_admin(client, auth_factory, db, "refund2-boss@example.com")
    customer = Customer(name="Refund Customer 2", tenant_id=1)
    db.add(customer)
    db.flush()
    order = Order(
        user_id=user_id, customer_id=customer.id, status="completed", tenant_id=1
    )
    db.add(order)
    db.flush()
    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=2,
        unit_price=Decimal("10.00"),
        tenant_id=1,
    )
    db.add(order_item)
    db.commit()

    resp = client.post(
        f"/admin/workflows/refund?step=items&order_id={order.id}",
        data={
            "step": "items",
            "reason": "oops",
            "payment_method": "cash",
            f"refund_qty_{order_item.id}": "99",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "step=items" in resp.headers["location"]
    db.expire_all()
    assert db.query(Refund).filter(Refund.order_id == order.id).count() == 0
