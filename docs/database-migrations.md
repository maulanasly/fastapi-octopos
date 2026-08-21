[Back to README](../README.md)

# Database & Migrations

This project includes Alembic migration files in `alembic/versions` — the
chain currently runs `0001` … `0019`. Revisions are zero-padded sequential
numbers (`0001_initial_schema.py`, `0002_...`, …); new migrations continue the
chain at the next number.

Run migrations:

```bash
make migrate
```

Apply/verify in the dev stack:

```bash
docker exec octopos-backend alembic upgrade head
docker exec octopos-backend python scripts/backfill_embeddings.py
```

## Migration 0015 — order tracking & embeddings

Requires the `pgvector/pgvector:pg16` image (adds the `vector` extension; also enables `cube` + `earthdistance`):

- Extensions: `cube`, `earthdistance`, `vector`
- `orders`: destination fields (`destination_address`, `destination_lat`, `destination_lng`, `destination point`), `tracking_status` (default `none`), transition timestamps; GiST index `ix_orders_destination_gist` for KNN/radius scans
- New table `order_location_updates` (tenant-scoped, lat/lng + `location point` + `source`); GiST index `ix_order_location_updates_location_gist`
- `products.embedding vector(384)` (nullable) + HNSW index `ix_products_embedding_hnsw`

## Later migrations

- **0016** — unique `localization_setting` per tenant
- **0017** — `supplier_payments` table (tenant-scoped, with review status)
- **0018** — `review_note` column on purchase orders (requester/approver reject feedback)
- **0019** — `purchasing_settings` table (per-tenant auto-PO settings)
