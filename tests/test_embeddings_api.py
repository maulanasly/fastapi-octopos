"""Semantic product search (pgvector embeddings): round-trip, ordering,
tenant isolation, HNSW index usage, and disabled-provider behavior."""

from sqlalchemy import text


def _make(client, headers, name, sku, description=""):
    cat = client.post(
        "/api/v1/products/categories",
        headers=headers,
        json={"name": "Embed", "description": "Seed"},
    )
    resp = client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "name": name,
            "sku": sku,
            "price": 50.0,
            "stock_quantity": 5,
            "min_stock": 0,
            "max_stock": 10,
            "reorder_point": 0,
            "lead_time_days": 0,
            "category_id": cat.json()["id"],
            "description": description,
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


class TestEmbeddingHooks:
    def test_product_create_stores_embedding(self, client, manager_headers):
        product = _make(
            client,
            manager_headers,
            "Premium Car Wax",
            "SKU-WAX1",
            "high-gloss polish and protection for vehicle paint",
        )
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            from app.models.product import Product

            row = db.get(Product, product["id"])
            assert row.embedding is not None
            assert len(row.embedding) == 384
            norm = sum(v * v for v in row.embedding) ** 0.5
            assert abs(norm - 1.0) < 1e-6  # unit vector
        finally:
            db.close()

    def test_update_reembeds(self, client, manager_headers):
        product = _make(client, manager_headers, "Battery Water", "SKU-BW1")
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            from app.models.product import Product

            row = db.get(Product, product["id"])
            before = list(row.embedding)
        finally:
            db.close()
        resp = client.put(
            f"/api/v1/products/{product['id']}",
            headers=manager_headers,
            json={"description": "distilled water refill for car batteries"},
        )
        assert resp.status_code == 200, resp.text
        db = SessionLocal()
        try:
            from app.models.product import Product

            row = db.get(Product, product["id"])
            assert row.embedding is not None
            assert list(row.embedding) != before
        finally:
            db.close()


class TestSearch:
    def test_semantic_search_returns_best_match_first(self, client, manager_headers):
        _make(
            client,
            manager_headers,
            "Premium Car Wax",
            "SKU-WAX2",
            "high-gloss polish for vehicle paint",
        )
        _make(
            client,
            manager_headers,
            "All-Purpose Cleaner",
            "SKU-CLN2",
            "multi-surface detergent spray",
        )
        resp = client.get(
            "/api/v1/products/search",
            headers=manager_headers,
            params={"q": "polish wax"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body, "expected at least one match"
        assert body[0]["name"] == "Premium Car Wax"

    def test_search_tenant_isolation(self, client, auth_factory, manager_headers):
        import _tenant_mode

        _tenant_mode.FORCE_DEFAULT_TENANT = False
        try:
            _make(client, manager_headers, "Tenant Product", "SKU-TEN1")
            other = auth_factory.user("search-other@example.com")
            resp = client.get(
                "/api/v1/products/search",
                headers=other,
                params={"q": "tenant product"},
            )
            assert resp.status_code == 200, resp.text
            assert resp.json() == []
        finally:
            _tenant_mode.FORCE_DEFAULT_TENANT = True

    def test_search_disabled_provider_returns_400(
        self, client, manager_headers, monkeypatch
    ):
        from app.core.config import settings

        monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "none")
        resp = client.get(
            "/api/v1/products/search",
            headers=manager_headers,
            params={"q": "anything"},
        )
        assert resp.status_code == 400, resp.text

    def test_hnsw_index_used(self, client, manager_headers, db):
        _make(client, manager_headers, "Indexed Product", "SKU-IDX1")
        from app.core.database import SessionLocal

        session = SessionLocal()
        try:
            session.execute(text("SET enable_seqscan = off"))
            rows = session.execute(
                text(
                    """
                    EXPLAIN (COSTS OFF)
                    SELECT id FROM products
                    ORDER BY embedding <=> '[0.1,0.2,0.3]'::vector
                    LIMIT 5
                    """
                )
            ).fetchall()
            assert any("ix_products_embedding_hnsw" in r[0] for r in rows), rows
        finally:
            session.close()
