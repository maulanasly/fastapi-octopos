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
