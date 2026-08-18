[Back to README](../README.md)

# API Overview

Base prefix: `/api/v1`

## Auth

- `POST /auth/register`
- `POST /auth/token`
- `POST /auth/refresh`
- `POST /auth/logout`
- `POST /auth/google`

## Products & Categories

- `GET /products/categories`
- `POST /products/categories`
- `GET /products/`
- `POST /products/` (embeds name+description when embeddings are configured)
- `PUT /products/{product_id}`
- `DELETE /products/{product_id}`
- `GET /products/search?q=` (semantic search over pgvector embeddings)

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
- `GET /rbac/roles`
- `POST /rbac/roles`
- `PUT /rbac/roles/{role_id}`
- `POST /rbac/users/{user_id}/roles`
- `GET /rbac/users/{user_id}/roles`
- `GET /rbac/me/permissions`

## Purchasing

- `GET /purchasing/suppliers`
- `POST /purchasing/suppliers`
- `PUT /purchasing/suppliers/{supplier_id}`
- `GET /purchasing/orders`
- `GET /purchasing/orders/{purchase_order_id}`
- `POST /purchasing/orders`
- `POST /purchasing/orders/from-replenishment`
- `POST /purchasing/orders/{purchase_order_id}/mark-ordered`
- `POST /purchasing/orders/{purchase_order_id}/receive`
- `POST /purchasing/orders/{purchase_order_id}/cancel`
- `GET /purchasing/invoices`
- `GET /purchasing/invoices/{invoice_id}`
- `POST /purchasing/invoices`
- `POST /purchasing/invoices/{invoice_id}/submit-review`
- `POST /purchasing/invoices/{invoice_id}/approve`
- `POST /purchasing/invoices/{invoice_id}/reject`

## Orders

- `GET /orders/`
- `POST /orders/` (supports optional `destination_address`, `destination_lat`, `destination_lng`)
- `GET /orders/serving/` and `GET /orders/serving/stream` (SSE: `serving` + `tracking` events)
- `GET /orders/tracking/` (requires `orders:track`)
- `POST /orders/tracking/{order_id}/status` (`assigned` | `en_route` | `on_site`, paid orders only)
- `POST /orders/tracking/{order_id}/location` (append position ping, broadcasts SSE)
- `GET /orders/tracking/nearest` (`lat`, `lng`, `radius_km`)
- `GET /orders/{order_id}/receipt`
- `POST /orders/{order_id}/payments`
- `POST /orders/{order_id}/payments/split`
- `POST /orders/{order_id}/cancel`
- `POST /orders/release-expired-reservations`

## Refunds

- `GET /refunds/`
- `GET /refunds/{refund_id}`
- `POST /refunds/`

## Sync

- `POST /sync/events/batch`

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
- `GET /reports/tax-liability`
