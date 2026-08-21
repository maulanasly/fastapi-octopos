[Back to README](../README.md)

# Development

## Project Structure

```text
app/
├── api/
│   ├── router.py          # Router aggregation
│   ├── dependencies.py    # require_permissions etc.
│   └── endpoints/         # Route handlers for each module
│       ├── audit.py       # Audit log querying
│       ├── auth.py        # Authentication (register, login, refresh, Google OAuth)
│       ├── customers.py
│       ├── drawers.py
│       ├── health.py      # Liveness/readiness probes
│       ├── inventory.py
│       ├── localization.py
│       ├── orders.py
│       ├── products.py
│       ├── promotions.py
│       ├── purchasing.py
│       ├── rbac.py
│       ├── refunds.py
│       ├── reports.py
│       ├── serving.py     # Serving queue + SSE stream
│       ├── sync.py
│       ├── taxes.py
│       ├── tracking.py    # Live order tracking (maps)
│       └── users.py
├── admin/                 # SQLAdmin views + workflows + custom form fields
├── core/                  # Shared utilities
│   ├── config.py          # Pydantic settings
│   ├── database.py        # SQLAlchemy engine/session
│   ├── security.py        # Password hashing, JWT utils
│   ├── limiter.py         # Rate limiting config
│   ├── rbac.py            # Role/permission helpers
│   ├── money.py           # Decimal precision helpers
│   ├── i18n.py            # t() translation helper
│   ├── audit.py           # Audit-log recording
│   ├── media.py           # Product image uploads
│   ├── observability.py   # Logging/middleware
│   ├── exclusive_task.py  # Single-runner task guard
│   ├── replenishment.py   # Replenishment suggestion logic
│   ├── validation.py
│   └── localization.py
├── models/                # SQLAlchemy models
├── schemas/               # Pydantic schemas
├── services/              # Business logic (orders, purchasing, serving, tracking, ...)
└── templates/             # SQLAdmin HTML templates
```

## Testing

Run the test suite:

```bash
make test
```

Run all quality checks (lint + tests + compile):

```bash
make check
```

## Regenerating admin screenshots

The screenshots embedded in the README come from the SQLAdmin panel and are
captured with Playwright:

```bash
make docker-dev                  # dev stack (source mounted) on :8000
make screenshots                 # installs dev deps + chromium, seeds demo data, captures docs/images/*.png
```

`scripts/seed_demo.sh` creates an idempotent demo dataset via the public API
(demo user, categories, products — including some below reorder point for the
restock workflow — customers, an open drawer, paid orders, a supplier, an
ordered PO, and an approved invoice). Point `BASE_URL` at any running stack
to target it, e.g. `BASE_URL=http://localhost:8001 make screenshots`.
