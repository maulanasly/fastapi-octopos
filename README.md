# FastAPI OctoPOS

A FastAPI-based Point of Sale (POS) backend with JWT auth, product/inventory management, order/payment flow, drawer sessions, reports, and SQLAdmin dashboard.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Make Commands](#make-commands)
- [Environment Variables](#environment-variables)
- [API Overview](#api-overview)
- [Admin Panel](#admin-panel)
- [Database & Migrations](#database--migrations)
- [License](#license)

## Features

### Authentication & Authorization

- Register with email/password
- OAuth2 login with JWT access token + refresh token
- Refresh token rotation and logout (token revocation)
- Google Sign-In (Google ID token)
- Rate-limited login endpoint (`10/minute`)
- Role-aware authorization:
  - Active-user protected APIs
  - Superuser-only report APIs

### Product & Category Management

- Category list and create
- Product CRUD (create, list, update, delete)
- Category validation on product creation
- SKU uniqueness at database level
- Replenishment settings per product (`min_stock`, `max_stock`, `reorder_point`, `lead_time_days`)
- Inventory movement logging for stock updates (`initial_stock`, `manual_adjustment`)

### Orders & Payments

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

### Localization & Regional Settings

- Centralized localization settings (`language`, `timezone`, `currency`, `date_format`, `number_format`, `country_code`)
- Translation-ready message layer with English and Indonesian keys for auth-related errors
- Shared currency/number/date formatting helpers for dashboard rendering

### Role-Based Access Control (RBAC)

- Role and permission entities with many-to-many assignments
- Default system roles: `cashier`, `manager`, `admin`
- Granular permission checks on sensitive modules (reports, taxes, purchasing approvals, localization updates, reservation release)
- User role assignment and self permission introspection APIs

### Refunds & Returns

- Create full or partial refunds from completed orders
- Validate refundable quantity per order item (prevents over-refund)
- Automatic stock restoration for refunded items
- Refund audit trail with reason, cashier, timestamp, and itemized lines
- Refund listing and detail endpoints with role-based access
- Idempotent refund creation via `idempotency_key`
- Inventory movement logging for refund restocking

### Customers & Loyalty

- Customer profile management (name/email/phone/status)
- Points balance tracking per customer
- Loyalty transactions ledger (`earn`, `redeem`, `adjust`)
- Automatic points earning on completed orders
- Automatic point restoration/reversal on order cancellation

### Promotions & Discounts

- Promotion management with code-based application
- Discount types: `percentage` and `fixed`
- Scope support: `order`, `product`, or `category`
- Eligibility controls: active window, minimum order amount, usage limit
- Discount tracking on order (`subtotal_amount`, `discount_amount`, `total_amount`)

### Tax Engine & Fiscal Receipt

- Tax rule management with scope support: `order`, `product`, `category`
- Tax modes: `exclusive` (added on top) and `inclusive` (embedded in base)
- Effective-date activation windows (`starts_at`, `ends_at`) and soft deactivation
- Persisted per-order tax lines for auditability and fiscal reporting

### Inventory Ledger

- Stock movement history endpoint with filters by product, movement type, user, and date range
- Tracks `quantity_before`, `quantity_delta`, and `quantity_after` for each movement
- Replenishment suggestion endpoint using sales velocity and lead-time projection

### Purchasing & Receiving

- Supplier management for replenishment workflow
- Purchase order creation with itemized quantity and unit cost
- Purchase order lifecycle: `draft`, `ordered`, `partially_received`, `received`, `cancelled`
- Receiving endpoint updates product stock and records `purchase_receipt` movements
- Purchase order auto-generation from replenishment suggestions
- Supplier invoice capture with PO item linkage
- 3-way matching-lite variance checks (`ordered` vs `received` vs `billed`)
- Invoice status workflow: `draft`, `pending_review`, `approved`, `rejected`

### Drawer Sessions

- Open drawer session
- Get current active drawer session
- Close drawer session
- Reconcile and close shift with expected vs counted cash/non-cash variance
- Enforce one open drawer session per user
- Track starting cash, ending cash, expected cash, opened/closed time

### Offline Sync & Idempotency

- Batch sync endpoint for offline POS clients (`/sync/events/batch`)
- Event types: `order_create`, `order_add_payment`, `refund_create`
- Per-event status response (`success`, `failed`, `duplicate`)
- Sync event logging for replay safety and audit trail

### Reports

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

### Admin Dashboard

- SQLAdmin panel at `/admin`
- Admin views for Users, Roles, Permissions, Customers, Loyalty Transactions, Categories, Products, Suppliers, Purchase Orders, Purchase Order Items, Purchase Invoices, Purchase Invoice Items, Orders, Order Items, Drawer Sessions, Shift Reconciliations, Stock Movements, Sync Event Logs
- Admin views include Promotions and Tax Rule management
- Custom reports page at `/admin/reports`
- Reports dashboard supports period presets (`today`, `7d`, `30d`, `month`, `all`) with aligned sales/refund/invoice summary scope

## Tech Stack

- **Backend:** FastAPI
- **ORM:** SQLAlchemy
- **Database:** SQLite
- **Migrations:** Alembic
- **Auth:** JWT (`python-jose`) + bcrypt hashing
- **Rate Limiting:** SlowAPI
- **Admin UI:** SQLAdmin

## Project Structure

```text
app/
  api/
    endpoints/
  core/
  models/
  schemas/
  admin/
  templates/
alembic/
```

## Getting Started

### 1. Clone repository

```bash
git clone https://github.com/maulanasly/fastapi-octopos.git
cd fastapi-octopos
```

### 2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
make install
```

### 4. Run the app

```bash
make run
```

Open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- Admin: `http://127.0.0.1:8000/admin`

## Make Commands

Common commands:

```bash
make help
make install
make run
make migrate
make makemigration MSG="add-refunds-table"
make lint
make check
```

## Environment Variables

Configuration is loaded from `.env` (see `app/core/config.py`).

Common variables:

```env
PROJECT_NAME=FastAPI POS Backend
API_V1_STR=/api/v1
SQLALCHEMY_DATABASE_URI=sqlite:///./sql_app.db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=11520
GOOGLE_CLIENT_ID=
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin
ORDER_RESERVATION_TIMEOUT_MINUTES=15
```

## API Overview

Base prefix: `/api/v1`

### Auth

- `POST /auth/register`
- `POST /auth/token`
- `POST /auth/refresh`
- `POST /auth/logout`
- `POST /auth/google`

### Products & Categories

- `GET /products/categories`
- `POST /products/categories`
- `GET /products/`
- `POST /products/`
- `PUT /products/{product_id}`
- `DELETE /products/{product_id}`

### Customers

- `GET /customers/`
- `POST /customers/`
- `GET /customers/{customer_id}`
- `PUT /customers/{customer_id}`
- `DELETE /customers/{customer_id}`
- `GET /customers/{customer_id}/orders`
- `GET /customers/{customer_id}/loyalty-transactions`

### Promotions

- `GET /promotions/`
- `POST /promotions/`
- `GET /promotions/{promotion_id}`
- `PUT /promotions/{promotion_id}`
- `DELETE /promotions/{promotion_id}`

### Inventory

- `GET /inventory/movements`
- `GET /inventory/replenishment-suggestions`

### Localization

- `GET /localization/`
- `PUT /localization/`

### Taxes

- `GET /taxes/`
- `POST /taxes/`
- `GET /taxes/{tax_rule_id}`
- `PUT /taxes/{tax_rule_id}`
- `DELETE /taxes/{tax_rule_id}`

### RBAC

- `POST /rbac/seed-defaults`
- `GET /rbac/roles`
- `POST /rbac/roles`
- `PUT /rbac/roles/{role_id}`
- `POST /rbac/users/{user_id}/roles`
- `GET /rbac/users/{user_id}/roles`
- `GET /rbac/me/permissions`

### Purchasing

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

### Orders

- `GET /orders/`
- `POST /orders/`
- `GET /orders/{order_id}/receipt`
- `POST /orders/{order_id}/payments`
- `POST /orders/{order_id}/payments/split`
- `POST /orders/{order_id}/cancel`
- `POST /orders/release-expired-reservations`

### Refunds

- `GET /refunds/`
- `GET /refunds/{refund_id}`
- `POST /refunds/`

### Sync

- `POST /sync/events/batch`

### Drawers

- `POST /drawers/open`
- `GET /drawers/active`
- `POST /drawers/close/{session_id}`
- `POST /drawers/reconcile/{session_id}`
- `GET /drawers/{session_id}/reconciliation`

### Reports (Superuser)

- `GET /reports/sales`
- `GET /reports/top-products`
- `GET /reports/top-customers`
- `GET /reports/categories`
- `GET /reports/low-stock`
- `GET /reports/purchase-invoices`
- `GET /reports/tax-liability`

## Admin Panel

- URL: `/admin`
- Uses session-based authentication with `ADMIN_USERNAME` and `ADMIN_PASSWORD`
- Includes a custom reports dashboard page at `/admin/reports`

## Database & Migrations

This project includes Alembic migration files in `alembic/versions`.

Run migrations:

```bash
make migrate
```

## License

MIT License. See [LICENSE](./LICENSE).
