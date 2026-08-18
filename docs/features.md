[Back to README](../README.md)

# Features

## Authentication & Authorization

- Register with email/password
- OAuth2 login with JWT access token + refresh token
- Refresh token rotation and logout (token revocation)
- Google Sign-In (Google ID token)
- Rate-limited login endpoint (`10/minute`)
- Role-aware authorization:
  - Active-user protected APIs
  - Superuser-only report APIs

## Product & Category Management

- Category list and create
- Product CRUD (create, list, update, delete)
- Category validation on product creation
- SKU uniqueness at database level
- Replenishment settings per product (`min_stock`, `max_stock`, `reorder_point`, `lead_time_days`)
- Inventory movement logging for stock updates (`initial_stock`, `manual_adjustment`)

## Orders & Payments

- Create multi-item orders
- Optional customer assignment on order
- Promotion code support with automatic discount calculation
- Loyalty points redemption on order creation
- Stock validation and automatic stock deduction on order creation
- Stock reservation lifecycle on pending orders (`reserved`, `released`, `committed`)
- Reservation expiry timestamp on order creation with configurable timeout
- Drawer session required before placing orders
- Attach payments to orders (supports partial payment)
- Atomic split-tender payment endpoint for multi-method checkout
- Settlement summary per order (`paid_amount`, `change_amount`, `remaining_amount`)
- Non-cash payment cannot exceed remaining amount; only cash can create change
- Idempotent order and payment writes via `idempotency_key`
- Auto-complete order when paid amount reaches/exceeds total
- Cancel order with automatic stock restoration
- Superuser endpoint to release expired unpaid reservations with stock restoration
- Order list filtering by user role (superuser vs own orders)
- Inventory movement logging for sales and order cancellations
- Tax-ready order totals (`taxable_base_amount`, `tax_total_amount`, `grand_total_amount`)
- Fiscal receipt endpoint with itemized tax/payment breakdown

## Localization & Regional Settings

- Centralized localization settings (`language`, `timezone`, `currency`, `date_format`, `number_format`, `country_code`)
- Per-user region presets (`US`, `ID`) overriding the global settings via `GET/PUT /localization/me`
- Translation-ready message layer with English and Indonesian keys for auth-related errors
- Shared currency/number/date formatting helpers for dashboard rendering

## Role-Based Access Control (RBAC)

- Role and permission entities with many-to-many assignments
- Default system roles: `cashier`, `manager`, `admin`
- Granular permission checks on sensitive modules (reports, taxes, purchasing approvals, localization updates, reservation release)
- User role assignment and self permission introspection APIs

## Refunds & Returns

- Create full or partial refunds from completed orders
- Validate refundable quantity per order item (prevents over-refund)
- Automatic stock restoration for refunded items
- Refund audit trail with reason, cashier, timestamp, and itemized lines
- Refund listing and detail endpoints with role-based access
- Idempotent refund creation via `idempotency_key`
- Inventory movement logging for refund restocking

## Customers & Loyalty

- Customer profile management (name/email/phone/status)
- Points balance tracking per customer
- Loyalty transactions ledger (`earn`, `redeem`, `adjust`)
- Automatic points earning on completed orders
- Automatic point restoration/reversal on order cancellation

## Promotions & Discounts

- Promotion management with code-based application
- Discount types: `percentage` and `fixed`
- Scope support: `order`, `product`, or `category`
- Eligibility controls: active window, minimum order amount, usage limit
- Discount tracking on order (`subtotal_amount`, `discount_amount`, `total_amount`)

## Tax Engine & Fiscal Receipt

- Tax rule management with scope support: `order`, `product`, `category`
- Tax modes: `exclusive` (added on top) and `inclusive` (embedded in base)
- Effective-date activation windows (`starts_at`, `ends_at`) and soft deactivation
- Persisted per-order tax lines for auditability and fiscal reporting

## Inventory Ledger

- Stock movement history endpoint with filters by product, movement type, user, and date range
- Tracks `quantity_before`, `quantity_delta`, and `quantity_after` for each movement
- Replenishment suggestion endpoint using sales velocity and lead-time projection

## Purchasing & Receiving

- Supplier management for replenishment workflow
- Purchase order creation with itemized quantity and unit cost
- Purchase order lifecycle: `draft`, `ordered`, `partially_received`, `received`, `cancelled`
- Receiving endpoint updates product stock and records `purchase_receipt` movements
- Purchase order auto-generation from replenishment suggestions
- Supplier invoice capture with PO item linkage
- 3-way matching-lite variance checks (`ordered` vs `received` vs `billed`)
- Invoice status workflow: `draft`, `pending_review`, `approved`, `rejected`

## Drawer Sessions

- Open drawer session
- Get current active drawer session
- Close drawer session
- Reconcile and close shift with expected vs counted cash/non-cash variance
- Enforce one open drawer session per user
- Track starting cash, ending cash, expected cash, opened/closed time

## Offline Sync & Idempotency

- Batch sync endpoint for offline POS clients (`/sync/events/batch`)
- Event types: `order_create`, `order_add_payment`, `refund_create`
- Per-event status response (`success`, `failed`, `duplicate`)
- Sync event logging for replay safety and audit trail

## Reports

Superuser-only APIs for:

- Sales summary (gross revenue, total refunds, net revenue, order count, average order value)
- Sales summary includes gross revenue and total discounts
- Top-selling products
- Top customers
- Category sales
- Low stock products
- Purchase invoice summary (counts, totals, variance, review pipeline)
- Tax liability summary by tax name/rate with period filtering
- Optional date-range filtering on sales analytics endpoints

## Admin Dashboard

- SQLAdmin panel at `/admin`
- Admin login authenticates against real app users: only active superusers may sign in (sessions expire after `ADMIN_SESSION_HOURS`, default 12h). In non-production environments the legacy `ADMIN_USERNAME`/`ADMIN_PASSWORD` credentials still work, to bootstrap the first admin account.
- To promote your first user to superuser in production: `UPDATE users SET is_superuser = 1 WHERE email = '...'` (or promote via the admin UI once another superuser exists)
- Admin views for Users, Roles, Permissions, Customers, Loyalty Transactions, Categories, Products, Suppliers, Purchase Orders, Purchase Order Items, Purchase Invoices, Purchase Invoice Items, Orders, Order Items, Drawer Sessions, Shift Reconciliations, Stock Movements, Sync Event Logs
- Admin views include Promotions and Tax Rule management
- Custom reports page at `/admin/reports`
- Reports dashboard supports period presets (`today`, `7d`, `30d`, `month`, `all`) with aligned sales/refund/invoice summary scope
- Reports are cached per period/locale (2 min TTL); amounts are rendered with the configured currency locale
- Low-stock warning uses each product's `reorder_point`/`min_stock` (default 10) instead of a hardcoded threshold
- Product stock is ledger-managed: `stock_quantity` is excluded from the create/edit forms; use the "Record Stock Adjustment" action on a product row to apply a delta and write an audited `StockMovement` entry
- System roles (`is_system`) cannot be edited or deleted from the admin UI
- Guided workflow wizards under `/admin/workflows`: Restock (auto-generate purchase orders and receive items), Invoicing (create, submit, approve/reject supplier invoices), Close Drawer (shift reconciliation), and Refund (item-level refunds from completed orders)
