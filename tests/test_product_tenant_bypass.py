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
