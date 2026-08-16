# FastAPI OctoPOS

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/maulanasly/fastapi-octopos/actions/workflows/ci.yml/badge.svg)](https://github.com/maulanasly/fastapi-octopos/actions/workflows/ci.yml)

A FastAPI-based Point of Sale (POS) backend with JWT auth, product/inventory management, order/payment flow, drawer sessions, reports, and SQLAdmin dashboard.

> **Note:** Copy `.env.example` to `.env` and update the values before running in production.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Make Commands](#make-commands)
- [Environment Variables](#environment-variables)
- [API Overview](#api-overview)
- [API Examples](#api-examples)
- [Admin Panel](#admin-panel)
- [Database & Migrations](#database--migrations)
- [Development](#development)
- [Deployment](#deployment)
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
- Per-user region presets (`US`, `ID`) overriding the global settings via `GET/PUT /localization/me`
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

### Prerequisites

- Python 3.10+
- Make (optional, for convenience commands)

### 1. Clone repository

```bash
git clone https://github.com/maulanasly/fastapi-octopos.git
cd fastapi-octopos
```

### 2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
make install
```

### 4. Configure environment

Copy `.env.example` and update the values as needed:

```bash
cp .env.example .env
```

### 5. Run migrations

The schema is managed exclusively by Alembic (the app no longer auto-creates tables at startup).

```bash
make migrate
```

> **Upgrading a database created before the migration squash:** the migration history was compacted into a single `0001_initial_schema` migration. Stamp existing databases with `alembic stamp 0001` after confirming their schema matches the current models (or re-run `alembic upgrade head` on a fresh database).

### 6. Run the app

```bash
make run
```

Open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- Admin: `http://127.0.0.1:8000/admin`

## Make Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make install` | Install project dependencies from requirements.txt |
| `make run` | Run API server with hot reload at http://127.0.0.1:8000 |
| `make dev` | Alias for `make run` |
| `make migrate` | Apply all database migrations |
| `make migrate-down` | Rollback last migration |
| `make makemigration MSG="description"` | Create new migration with description |
| `make lint` | Run pre-commit code quality checks |
| `make format` | Auto-format code with black and isort |
| `make test` | Run test suite with pytest |
| `make pre-commit` | Install pre-commit git hooks |
| `make clean` | Remove Python cache files |

## Environment Variables

Configuration is loaded from `.env` (see `app/core/config.py`). Copy `.env.example` to `.env` and update the values before running:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_NAME` | Application name | `FastAPI POS Backend` |
| `API_V1_STR` | API prefix | `/api/v1` |
| `ENVIRONMENT` | `development` or `production` — production refuses default secrets | `development` |
| `BACKEND_CORS_ORIGINS` | CORS allowed origins (JSON array) | `["http://localhost:3001", "http://localhost:8080"]` |
| `SQLALCHEMY_DATABASE_URI` | Database connection string | `sqlite:///./sql_app.db` |
| `SECRET_KEY` | JWT signing secret (change in production) | Random default (insecure) |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime in minutes | `11520` (8 days) |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID (optional) | `None` |
| `ADMIN_USERNAME` | Admin panel username | `admin` |
| `ADMIN_PASSWORD` | Admin panel password | `admin` (change in production) |
| `ORDER_RESERVATION_TIMEOUT_MINUTES` | Stock reservation expiry | `15` |
| `RESERVATION_AUTO_EXPIRE_ENABLED` | Periodic + startup sweep of expired reservations (required in production when reservations are on) | `False` |
| `RESERVATION_AUTO_EXPIRE_INTERVAL_SECONDS` | Sweep interval | `300` |
| `DEFAULT_TAX_RATE` | Rate for the migration-seeded default tax rule | `0.0` |
| `DEFAULT_TAX_NAME` | Name for the migration-seeded default tax rule | `VAT` |
| `LOGIN_MAX_ATTEMPTS` | Failed logins before temporary lockout | `5` |
| `LOGIN_LOCKOUT_MINUTES` | Lockout duration after repeated failures | `15` |
| `REPLENISHMENT_AUTO_PO_ENABLED` | Scheduled auto-generation of draft purchase orders from reorder points | `False` |
| `REPLENISHMENT_CHECK_INTERVAL_SECONDS` | Auto-PO check interval | `3600` |
| `REPLENISHMENT_LOOKBACK_DAYS` | Sales lookback for replenishment velocity | `30` |
| `LOG_LEVEL` | Logging level (`DEBUG`, `INFO`, ...) | `INFO` |
| `LOG_JSON` | Emit JSON log lines (production-friendly) | `False` |

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

- `GET /localization/` — global (admin) settings
- `PUT /localization/` — update global settings (requires `settings:manage`)
- `GET /localization/regions` — supported regional presets (`US`, `ID`)
- `GET /localization/me` — effective per-user settings (preset or global)
- `PUT /localization/me` — switch the caller's region preset (`{"region": "ID"}`; `null` resets to the global default)

Region presets bundle language, timezone, currency, and date/number
formats. The Flutter client renders money/dates and UI strings from these
settings and sends `Accept-Language` so API errors arrive translated.

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

## API Examples

### Authentication

**Register a new user:**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "full_name": "User Name",
    "password": "secure-password"
  }'
```

**Login (get JWT tokens):**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=secure-password"
```

### Create Order

```bash
curl -X POST http://127.0.0.1:8000/api/v1/orders/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"product_id": 1, "quantity": 2},
      {"product_id": 2, "quantity": 1}
    ],
    "customer_id": 1
  }'
```

### Add Payment

```bash
curl -X POST http://127.0.0.1:8000/api/v1/orders/1/payments \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50000,
    "payment_method": "cash"
  }'
```

### Sync Events (Offline Clients)

```bash
curl -X POST http://127.0.0.1:8000/api/v1/sync/events/batch \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "client_event_id": "evt-001",
        "event_type": "order_create",
        "payload": {
          "items": [{"product_id": 1, "quantity": 1}],
          "idempotency_key": "order-001"
        }
      }
    ]
  }'
```

### Pull Sync (Terminals)

Offline terminals pull catalog changes and check their event queue:

```bash
# Delta catalog since a watermark (omit ?since= for a full first sync)
curl -G http://127.0.0.1:8000/api/v1/sync/catalog \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  --data-urlencode "since=2026-08-16T00:00:00Z"

# Status of processed offline events
curl http://127.0.0.1:8000/api/v1/sync/events?status=success \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Health & Operations

```bash
curl http://127.0.0.1:8000/api/v1/health        # liveness
curl http://127.0.0.1:8000/api/v1/health/ready  # readiness (DB check)
```

Every response carries an `X-Request-ID` header echoed into log lines
(`request_id=...`) for request correlation.

### Audit Trail

Sensitive operations (refunds, stock adjustments, drawer reconciliation,
RBAC changes) are recorded in `audit_logs`. Superusers query them via:

```bash
curl http://127.0.0.1:8000/api/v1/audit/logs?action=refund.create \
  -H "Authorization: Bearer SUPERUSER_TOKEN"
```

### Shift Reports (Z-Reports)

```bash
# JSON Z-report for one closed shift
curl http://127.0.0.1:8000/api/v1/reports/shift/{reconciliation_id} \
  -H "Authorization: Bearer TOKEN"

# End-of-day summary across shifts
curl "http://127.0.0.1:8000/api/v1/reports/daily-close?report_date=2026-08-16" \
  -H "Authorization: Bearer TOKEN"
```

Print-friendly versions are available in the admin dashboard
(`/admin/reports` -> "Shift Reports").

## Development

### Project Structure

```text
app/
├── api/
│   └── endpoints/     # Route handlers for each module
│       ├── auth.py    # Authentication (register, login, refresh, Google OAuth)
│       ├── customers.py
│       ├── drawers.py
│       ├── inventory.py
│       ├── localization.py
│       ├── orders.py
│       ├── products.py
│       ├── promotions.py
│       ├── purchasing.py
│       ├── rbac.py
│       ├── refunds.py
│       ├── reports.py
│       ├── sync.py
│       └── taxes.py
├── admin/            # SQLAdmin views
├── core/           # Shared utilities
│   ├── config.py     # Pydantic settings
│   ├── database.py   # SQLAlchemy engine/session
│   ├── security.py   # Password hashing, JWT utils
│   ├── limiter.py    # Rate limiting config
│   ├── rbac.py       # Role/permission helpers
│   ├── money.py      # Decimal precision helpers
│   └── localization.py
├── models/         # SQLAlchemy models
├── schemas/        # Pydantic schemas
└── templates/      # SQLAdmin HTML templates
```

### Testing

> **Note:** The test suite is configured but test files are not yet implemented.

To run tests when they are added:

```bash
make test
```

Run all quality checks (lint + tests + compile):

```bash
make check
```

## Deployment

For production deployment:

1. Change `SECRET_KEY` to a secure random value
2. Update `ADMIN_PASSWORD` to a strong password
3. Set `BACKEND_CORS_ORIGINS` to your frontend domain
4. Use a production database (PostgreSQL recommended)
5. Set `GOOGLE_CLIENT_ID` if using Google Sign-In
