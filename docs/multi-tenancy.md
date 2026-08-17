# Multi-tenancy Design

Status: implemented on `feat/multi-tenant` (stacked on `feat/scale-hardening`).

## Model: shared schema, one row per tenant

All tenants share one PostgreSQL database. Every table holding business data
carries a `tenant_id` column referencing `tenants`; rows are isolated by that
column, and uniqueness constraints are scoped per tenant.

Isolation model: shared schema + `tenant_id` (chosen over per-schema or
per-database isolation — right-sized for a POS SaaS at this scale).

## Tenant vs global tables

| Category | Tables |
|---|---|
| Global (no tenant_id) | `tenants`, `roles`, `permissions`, `role_permissions`, `alembic_version` |
| Tenant-scoped | `users` (nullable — platform superuser has none), `categories`, `products`, `customers`, `promotions`, `tax_rules`, `orders`, `order_items`, `order_tax_lines`, `payments`, `refunds`, `refund_items`, `drawer_sessions`, `shift_reconciliations`, `stock_movements`, `loyalty_transactions`, `purchase_orders`, `purchase_order_items`, `purchase_invoices`, `purchase_invoice_items`, `sync_event_logs`, `audit_logs`, `localization_settings`, `refresh_tokens` |

Child rows (order items, refund items, PO lines, tax lines, payments, stock
movements, loyalty transactions) denormalize `tenant_id` so every lookup is a
single-table filter — no parent join required and no way to leak rows through
a direct child lookup.

## Uniqueness

- `users.email`: global unique dropped. New partial unique index on
  `(tenant_id, email) WHERE tenant_id IS NOT NULL` — the same staff email can
  exist in different tenants. Superuser emails (tenant_id NULL) are enforced
  unique by a partial index `ON email WHERE tenant_id IS NULL`.
- `products.sku`: global unique → unique `(tenant_id, sku)`.
- `promotions.code`: global unique → unique `(tenant_id, code)`.
- `orders (user_id, idempotency_key)` / `payments` / `refunds`: unchanged —
  users are already tenant-bound, so these are per-tenant by construction.

## Users and auth

- Every staff user belongs to exactly one tenant (`users.tenant_id` NOT NULL).
- Platform superuser (`is_superuser = true`) has `tenant_id NULL` and can read
  across tenants (existing superuser short-circuits in queries stay).
- `POST /auth/register` creates a **tenant + its first user**, who becomes the
  tenant owner (admin role). Subsequent staff are added by the owner/manager
  through the admin panel (admin UI binds new users to the admin's tenant).
- JWT gains a `ten` claim (tenant id). API-scoping dependency
  `get_current_tenant` reads it; endpoints filter on `tenant_id`.
- Login: email lookup may match users in multiple tenants → the login form
  accepts an optional tenant identifier; when ambiguous, the API returns 400
  telling the client to specify it.

## Data migration

Alembic migration `0011` creates `tenants`, adds `tenant_id` to every
tenant-scoped table, backfills all existing rows to tenant **1** (created as
"Default Business"), converts the global uniques to per-tenant partial
indexes, and drops the old global indexes.

The `scripts/migrate_sqlite_to_postgres.py` copy injects `tenant_id = 1` for
any target column the SQLite source lacks, so old SQLite DBs land in tenant 1
as well.

## Cross-cutting

- Reports cache keys include the tenant id (no cross-tenant cache hits).
- `get_shift_list_data`, admin audit viewer, sync endpoints, and the
  reservation sweep are all tenant-filtered (sweep scoped by the acting
  superuser's tenant via the JWT claim).
- RBAC (roles/permissions) stays global; `user_roles` is global too (the
  user row already carries the tenant).