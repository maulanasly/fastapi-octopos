# FastAPI OctoPOS

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/maulanasly/fastapi-octopos/actions/workflows/ci.yml/badge.svg)](https://github.com/maulanasly/fastapi-octopos/actions/workflows/ci.yml)

A FastAPI-based Point of Sale (POS) backend with JWT auth, product/inventory management, order/payment flow, drawer sessions, reports, and SQLAdmin dashboard.

> **Note:** Copy `.env.example` to `.env` and update the values before running in production.

## Table of Contents

- [Features](docs/features.md)
- [Tech Stack](docs/tech-stack.md)
- [Getting Started](docs/getting-started.md)
- [Make Commands](docs/make-commands.md)
- [Environment Variables](docs/environment-variables.md)
- [API Overview](docs/api-overview.md)
- [API Examples](docs/api-examples.md)
- [Admin Panel](docs/admin-panel.md)
- [Database & Migrations](docs/database-migrations.md)
- [Development](docs/development.md)
- [Deployment](docs/deployment.md)

## Quick Start

```bash
git clone https://github.com/maulanasly/fastapi-octopos.git
cd fastapi-octopos
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
make install
cp .env.example .env
make migrate
make run
```

Open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- Admin: `http://127.0.0.1:8000/admin`

See [Getting Started](docs/getting-started.md) for the full guide.

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

## License

MIT License. See [LICENSE](./LICENSE).
