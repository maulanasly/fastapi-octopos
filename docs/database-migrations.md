[Back to README](../README.md)

# Database & Migrations

This project includes Alembic migration files in `alembic/versions`.

Run migrations:

```bash
make migrate
```

## Migration 0015 — order tracking & embeddings

Requires the `pgvector/pgvector:pg16` image (adds the `vector` extension; also enables `cube` + `earthdistance`):

- Extensions: `cube`, `earthdistance`, `vector`
- `orders`: destination fields (`destination_address`, `destination_lat`, `destination_lng`, `destination point`), `tracking_status` (default `none`), transition timestamps; GiST index `ix_orders_destination_gist` for KNN/radius scans
- New table `order_location_updates` (tenant-scoped, lat/lng + `location point` + `source`); GiST index `ix_order_location_updates_location_gist`
- `products.embedding vector(384)` (nullable) + HNSW index `ix_products_embedding_hnsw`

Apply/verify in the dev stack:

```bash
docker exec octopos-backend alembic upgrade head
docker exec octopos-backend python scripts/backfill_embeddings.py
```
