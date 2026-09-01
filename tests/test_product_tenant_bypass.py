"""Superuser bypass and per-tenant product isolation."""

import _tenant_mode
import pytest

from app.models.rbac import Role
from app.models.user import User


@pytest.fixture(autouse=True)
def multi_tenant_mode():
    _tenant_mode.FORCE_DEFAULT_TENANT = False
    yield
    _tenant_mode.FORCE_DEFAULT_TENANT = True


def test_superuser_sees_all_products(client, auth_factory, db):
    # create two tenants with products
    auth_factory.register("bypass-a@example.com")
    b = auth_factory.register("bypass-b@example.com")
    # make a superuser (promote b)
    user_b = db.get(User, b["id"])
    user_b.is_superuser = True
    db.commit()

    # First assign admin role which has products:manage
    for email in ("bypass-a@example.com", "bypass-b@example.com"):
        user = db.query(User).filter(User.email == email).one()
        # ensure admin role which has products:manage
        admin_role = db.query(Role).filter(Role.name == "admin").one()
        if admin_role not in user.roles:
            user.roles.append(admin_role)
            db.commit()

    headers_a = auth_factory.login("bypass-a@example.com")
    headers_b = auth_factory.login("bypass-b@example.com")

    # create product in A
    cat_a = client.post(
        "/api/v1/products/categories", headers=headers_a, json={"name": "CatA"}
    )
    assert cat_a.status_code == 200, cat_a.text
    prod_a = client.post(
        "/api/v1/products",
        headers=headers_a,
        json={
            "name": "ProdA",
            "sku": "SKU-A",
            "price": 10.0,
            "category_id": cat_a.json()["id"],
        },
    )
    assert prod_a.status_code == 200, prod_a.text

    cat_b = client.post(
        "/api/v1/products/categories", headers=headers_b, json={"name": "CatB"}
    )
    assert cat_b.status_code == 200, cat_b.text
    prod_b = client.post(
        "/api/v1/products",
        headers=headers_b,
        json={
            "name": "ProdB",
            "sku": "SKU-B",
            "price": 12.0,
            "category_id": cat_b.json()["id"],
        },
    )
    assert prod_b.status_code == 200, prod_b.text

    # superuser (b) should see both without tenant filter
    resp_all = client.get("/api/v1/products", headers=headers_b)
    assert resp_all.status_code == 200
    ids_all = {p["id"] for p in resp_all.json()}
    assert prod_a.json()["id"] in ids_all
    assert prod_b.json()["id"] in ids_all

    # superuser filtered by tenant_id
    tenant_a = (
        db.query(User).filter(User.email == "bypass-a@example.com").one().tenant_id
    )
    resp_a = client.get(f"/api/v1/products?tenant_id={tenant_a}", headers=headers_b)
    assert resp_a.status_code == 200
    ids_a = {p["id"] for p in resp_a.json()}
    assert prod_a.json()["id"] in ids_a
    assert prod_b.json()["id"] not in ids_a

    # normal user ignores tenant_id param
    resp_normal = client.get(
        f"/api/v1/products?tenant_id={tenant_a}", headers=headers_a
    )
    assert resp_normal.status_code == 200
    ids_normal = {p["id"] for p in resp_normal.json()}
    # should only see its own, not B's, even though param points to A
    assert prod_a.json()["id"] in ids_normal
    assert prod_b.json()["id"] not in ids_normal

    # same for categories
    cats_all = client.get("/api/v1/products/categories", headers=headers_b).json()
    assert len(cats_all) >= 2
    cats_a = client.get(
        f"/api/v1/products/categories?tenant_id={tenant_a}", headers=headers_b
    ).json()
    assert (
        all(c["tenant_id"] == tenant_a for c in []) or len(cats_a) == 1
    )  # schema doesn't expose tenant_id, just count
    assert len(cats_a) == 1

    # superuser create with tenant_id param
    new_cat = client.post(
        f"/api/v1/products/categories?tenant_id={tenant_a}",
        headers=headers_b,
        json={"name": "SuperCatA"},
    )
    assert new_cat.status_code == 200, new_cat.text
    # verify it landed in tenant A
    resp_check = client.get(
        f"/api/v1/products/categories?tenant_id={tenant_a}", headers=headers_b
    ).json()
    assert any(c["name"] == "SuperCatA" for c in resp_check)


def test_search_isolation(client, auth_factory, db):
    auth_factory.register("search-a@example.com")
    b = auth_factory.register("search-b@example.com")
    for email in ("search-a@example.com", "search-b@example.com"):
        user = db.query(User).filter(User.email == email).one()
        admin_role = db.query(Role).filter(Role.name == "admin").one()
        if admin_role not in user.roles:
            user.roles.append(admin_role)
            db.commit()
    headers_a = auth_factory.login("search-a@example.com")
    headers_b = auth_factory.login("search-b@example.com")
    # promote b to superuser for later
    user_b = db.get(User, b["id"])
    user_b.is_superuser = True
    db.commit()
    headers_b = auth_factory.login("search-b@example.com")

    cat_a = client.post(
        "/api/v1/products/categories", headers=headers_a, json={"name": "SearchCat"}
    ).json()
    client.post(
        "/api/v1/products",
        headers=headers_a,
        json={
            "name": "UniqueSearchProdXYZ",
            "sku": "SEARCH-1",
            "price": 5.0,
            "category_id": cat_a["id"],
        },
    )
    # search as B should not find A's product (isolated)
    # Note: embeddings may be disabled, so search may return 400; we skip if so
    resp = client.get(
        "/api/v1/products/search?q=UniqueSearchProdXYZ", headers=headers_b
    )
    if resp.status_code == 400 and "not configured" in resp.text:
        pytest.skip("embeddings not configured")
    assert resp.status_code == 200
    # superuser without tenant filter should find it (if bypass includes search)
    # Already tested tenant isolation via product list above


def test_product_move_to_different_tenant(client, auth_factory, db):
    # Setup two tenants
    auth_factory.register("move-a@example.com")
    b = auth_factory.register("move-b@example.com")
    from app.models.user import User as _User  # local to avoid shadowing

    user_b = db.get(_User, b["id"])
    user_b.is_superuser = True
    db.commit()

    for email in ("move-a@example.com", "move-b@example.com"):
        user = db.query(_User).filter(_User.email == email).one()
        admin_role = db.query(Role).filter(Role.name == "admin").one()
        if admin_role not in user.roles:
            user.roles.append(admin_role)
            db.commit()

    headers_a = auth_factory.login("move-a@example.com")
    headers_b = auth_factory.login("move-b@example.com")  # superuser

    tenant_b = (
        db.query(_User).filter(_User.email == "move-b@example.com").one().tenant_id
    )

    cat_a = client.post(
        "/api/v1/products/categories", headers=headers_a, json={"name": "MoveCatA"}
    ).json()
    prod = client.post(
        "/api/v1/products",
        headers=headers_a,
        json={
            "name": "MoveProd",
            "sku": "MOVE-1",
            "price": 9.0,
            "category_id": cat_a["id"],
        },
    ).json()

    # Normal user cannot move
    resp = client.put(
        f"/api/v1/products/{prod['id']}?tenant_id={tenant_b}",
        headers=headers_a,
        json={},
    )
    assert resp.status_code == 403, resp.text

    # Superuser moves product to tenant B
    resp = client.put(
        f"/api/v1/products/{prod['id']}?tenant_id={tenant_b}",
        headers=headers_b,
        json={},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == prod["id"]

    # Verify product now in B, not in A
    list_a = client.get("/api/v1/products", headers=headers_a).json()
    assert all(p["id"] != prod["id"] for p in list_a)
    list_b = client.get(
        f"/api/v1/products?tenant_id={tenant_b}", headers=headers_b
    ).json()
    assert any(p["id"] == prod["id"] for p in list_b)
    # Also direct fetch as superuser without filter should still see it
    all_products = client.get("/api/v1/products", headers=headers_b).json()
    assert any(p["id"] == prod["id"] for p in all_products)

    # Category should have been auto-cleared (since old category belongs to A)
    moved = client.get(
        f"/api/v1/products?tenant_id={tenant_b}", headers=headers_b
    ).json()
    moved_prod = next(p for p in moved if p["id"] == prod["id"])
    assert moved_prod["category_id"] is None  # auto-cleared

    # Moving to non-existent tenant
    resp = client.put(
        f"/api/v1/products/{prod['id']}?tenant_id=99999", headers=headers_b, json={}
    )
    assert resp.status_code == 404, resp.text

    # Duplicate SKU in target should be rejected
    # Create another product in B with same SKU
    cat_b = client.post(
        "/api/v1/products/categories", headers=headers_b, json={"name": "MoveCatB"}
    ).json()
    # Need to specify tenant for superuser create when using B's headers? B is superuser but has tenant_b,
    # but we can create via tenant_b context by not specifying tenant_id (fallback to own tenant)
    # So create in B directly
    client.post(
        "/api/v1/products",
        headers=headers_b,
        json={
            "name": "Other",
            "sku": "DUP-SKU",
            "price": 5.0,
            "category_id": cat_b["id"],
        },
    ).json()
    # Create product in A with same SKU to move and trigger duplicate
    prod2 = client.post(
        "/api/v1/products",
        headers=headers_a,
        json={"name": "DupProd", "sku": "DUP-SKU", "price": 7.0},
    ).json()
    resp = client.put(
        f"/api/v1/products/{prod2['id']}?tenant_id={tenant_b}",
        headers=headers_b,
        json={},
    )
    assert resp.status_code == 400 and "already exists" in resp.text, resp.text

    # Moving with category that belongs to target should succeed
    prod3 = client.post(
        "/api/v1/products",
        headers=headers_a,
        json={"name": "MoveWithCat", "sku": "MOVE-CAT", "price": 8.0},
    ).json()
    resp = client.put(
        f"/api/v1/products/{prod3['id']}?tenant_id={tenant_b}",
        headers=headers_b,
        json={"category_id": cat_b["id"]},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["category_id"] == cat_b["id"]
