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
- Inventory movement logging for stock updates (`initial_stock`, `manual_adjustment`)

### Orders & Payments

- Create multi-item orders
- Stock validation and automatic stock deduction on order creation
- Drawer session required before placing orders
- Attach payments to orders (supports partial payment)
- Auto-complete order when paid amount reaches/exceeds total
- Cancel order with automatic stock restoration
- Order list filtering by user role (superuser vs own orders)
- Inventory movement logging for sales and order cancellations

### Refunds & Returns

- Create full or partial refunds from completed orders
- Validate refundable quantity per order item (prevents over-refund)
- Automatic stock restoration for refunded items
- Refund audit trail with reason, cashier, timestamp, and itemized lines
- Refund listing and detail endpoints with role-based access
- Inventory movement logging for refund restocking

### Inventory Ledger

- Stock movement history endpoint with filters by product, movement type, user, and date range
- Tracks `quantity_before`, `quantity_delta`, and `quantity_after` for each movement

### Purchasing & Receiving

- Supplier management for replenishment workflow
- Purchase order creation with itemized quantity and unit cost
- Purchase order lifecycle: `draft`, `ordered`, `partially_received`, `received`, `cancelled`
- Receiving endpoint updates product stock and records `purchase_receipt` movements

### Drawer Sessions

- Open drawer session
- Get current active drawer session
- Close drawer session
- Reconcile and close shift with expected vs counted cash/non-cash variance
- Enforce one open drawer session per user
- Track starting cash, ending cash, expected cash, opened/closed time

### Reports

Superuser-only APIs for:

- Sales summary (gross revenue, total refunds, net revenue, order count, average order value)
- Top-selling products
- Category sales
- Low stock products
- Optional date-range filtering on sales analytics endpoints

### Admin Dashboard

- SQLAdmin panel at `/admin`
- Admin views for Users, Categories, Products, Suppliers, Purchase Orders, Purchase Order Items, Orders, Order Items, Drawer Sessions, Shift Reconciliations, Stock Movements
- Custom reports page at `/admin/reports`

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

### Inventory

- `GET /inventory/movements`

### Purchasing

- `GET /purchasing/suppliers`
- `POST /purchasing/suppliers`
- `PUT /purchasing/suppliers/{supplier_id}`
- `GET /purchasing/orders`
- `GET /purchasing/orders/{purchase_order_id}`
- `POST /purchasing/orders`
- `POST /purchasing/orders/{purchase_order_id}/mark-ordered`
- `POST /purchasing/orders/{purchase_order_id}/receive`
- `POST /purchasing/orders/{purchase_order_id}/cancel`

### Orders

- `GET /orders/`
- `POST /orders/`
- `POST /orders/{order_id}/payments`
- `POST /orders/{order_id}/cancel`

### Refunds

- `GET /refunds/`
- `GET /refunds/{refund_id}`
- `POST /refunds/`

### Drawers

- `POST /drawers/open`
- `GET /drawers/active`
- `POST /drawers/close/{session_id}`
- `POST /drawers/reconcile/{session_id}`
- `GET /drawers/{session_id}/reconciliation`

### Reports (Superuser)

- `GET /reports/sales`
- `GET /reports/top-products`
- `GET /reports/categories`
- `GET /reports/low-stock`

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
