[Back to README](../README.md)

# API Overview

Base prefix: `/api/v1`

## Auth

- `POST /auth/register`
- `POST /auth/token`
- `GET /auth/me`
- `POST /auth/refresh`
- `POST /auth/logout`
- `POST /auth/google`

## Products & Categories

- `GET /products/categories`
- `POST /products/categories`
- `GET /products/categories/colors`
- `PUT /products/categories/{category_id}`
- `DELETE /products/categories/{category_id}`
- `GET /products/`
- `POST /products/` (embeds name+description when embeddings are configured)
- `PUT /products/{product_id}`
- `DELETE /products/{product_id}`
- `GET /products/search?q=` (semantic search over pgvector embeddings)
- `POST /products/{product_id}/image`
- `DELETE /products/{product_id}/image`

## Customers

- `GET /customers/`
- `POST /customers/`
- `GET /customers/{customer_id}`
- `PUT /customers/{customer_id}`
- `DELETE /customers/{customer_id}`
- `GET /customers/{customer_id}/orders`
- `GET /customers/{customer_id}/loyalty-transactions`

## Promotions

- `GET /promotions/`
- `POST /promotions/`
- `GET /promotions/{promotion_id}`
- `PUT /promotions/{promotion_id}`
- `DELETE /promotions/{promotion_id}`

## Inventory

- `GET /inventory/movements`
- `GET /inventory/replenishment-suggestions`

## Localization

- `GET /localization/` — global (admin) settings
- `PUT /localization/` — update global settings (requires `settings:manage`)
- `GET /localization/regions` — supported regional presets (`US`, `ID`)
- `GET /localization/options` — effective options for the caller (preset or global)
- `GET /localization/me` — effective per-user settings (preset or global)
- `PUT /localization/me` — switch the caller's region preset (`{"region": "ID"}`; `null` resets to the global default)

Region presets bundle language, timezone, currency, and date/number
formats. The Flutter client renders money/dates and UI strings from these
settings and sends `Accept-Language` so API errors arrive translated.

## Taxes

- `GET /taxes/`
- `POST /taxes/`
- `GET /taxes/{tax_rule_id}`
- `PUT /taxes/{tax_rule_id}`
- `DELETE /taxes/{tax_rule_id}`

## RBAC

- `POST /rbac/seed-defaults`
- `GET /rbac/permissions`
- `GET /rbac/roles`
- `POST /rbac/roles`
- `PUT /rbac/roles/{role_id}`
- `POST /rbac/users/{user_id}/roles`
- `GET /rbac/users/{user_id}/roles`
- `GET /rbac/me/permissions`

## Purchasing

### Suppliers

- `GET /purchasing/suppliers`
- `POST /purchasing/suppliers`
- `PUT /purchasing/suppliers/{supplier_id}`
- `GET /purchasing/suppliers/{supplier_id}/ledger` — supplier ledger of orders, invoices, and payments

### Purchase orders

- `GET /purchasing/orders`
- `GET /purchasing/orders/{purchase_order_id}`
- `GET /purchasing/orders/{purchase_order_id}/detail` — consolidated PO detail with item costs vs invoice variance
- `POST /purchasing/orders`
- `POST /purchasing/orders/from-replenishment`
- `POST /purchasing/orders/{purchase_order_id}/submit-review`
- `POST /purchasing/orders/{purchase_order_id}/mark-ordered`
- `POST /purchasing/orders/{purchase_order_id}/receive`
- `POST /purchasing/orders/{purchase_order_id}/reject`
- `POST /purchasing/orders/{purchase_order_id}/cancel`

### Invoices

- `GET /purchasing/invoices`
- `GET /purchasing/invoices/{invoice_id}`
- `POST /purchasing/invoices`
- `POST /purchasing/invoices/{invoice_id}/submit-review`
- `POST /purchasing/invoices/{invoice_id}/approve`
- `POST /purchasing/invoices/{invoice_id}/reject`

### Supplier payments

- `GET /purchasing/payments`
- `POST /purchasing/payments`
- `POST /purchasing/payments/{payment_id}/submit-review`
- `POST /purchasing/payments/{payment_id}/approve`
- `POST /purchasing/payments/{payment_id}/reject`

### Settings

- `GET /purchasing/settings` — per-tenant auto-PO settings
- `PUT /purchasing/settings` — update auto-PO thresholds (`REPLENISHMENT_*`)

## Orders

- `GET /orders/`
- `POST /orders/` (supports optional `destination_address`, `destination_lat`, `destination_lng`)
- `GET /orders/{order_id}/receipt`
- `POST /orders/{order_id}/payments`
- `POST /orders/{order_id}/payments/split`
- `POST /orders/{order_id}/cancel`
- `POST /orders/release-expired-reservations`

## Serving queue

- `GET /orders/serving/`
- `GET /orders/serving/stream` (SSE: `serving` + `tracking` events)
- `POST /orders/serving/{order_id}/start`
- `POST /orders/serving/{order_id}/ready`
- `POST /orders/serving/{order_id}/serve`

## Tracking

- `GET /orders/tracking/` (requires `orders:track`)
- `POST /orders/tracking/{order_id}/status` (`assigned` | `en_route` | `on_site`, paid orders only)
- `POST /orders/tracking/{order_id}/location` (append position ping, broadcasts SSE)
- `GET /orders/tracking/nearest` (`lat`, `lng`, `radius_km`)

## Refunds

- `GET /refunds/`
- `GET /refunds/{refund_id}`
- `POST /refunds/`

## Drawers

- `POST /drawers/open`
- `GET /drawers/active`
- `POST /drawers/close/{session_id}`
- `POST /drawers/reconcile/{session_id}`
- `GET /drawers/{session_id}/reconciliation`

## Reports (Superuser)

- `GET /reports/sales`
- `GET /reports/top-products`
- `GET /reports/top-customers`
- `GET /reports/categories`
- `GET /reports/low-stock`
- `GET /reports/purchase-invoices`
- `GET /reports/supplier-payments`
- `GET /reports/supplier-spend`
- `GET /reports/purchase-variance`
- `GET /reports/tax-liability`
- `GET /reports/shifts`
- `GET /reports/shift/{reconciliation_id}`
- `GET /reports/daily-close`

## Sync

- `GET /sync/catalog` — full tenant catalog export
- `GET /sync/events` — sync event log
- `POST /sync/events/batch`

## Health

- `GET /health` — liveness probe
- `GET /health/ready` — readiness probe (checks database connectivity)

## Audit

- `GET /audit/logs`

## Users

- `GET /users/`
- `POST /users/`
- `PUT /users/{user_id}`
