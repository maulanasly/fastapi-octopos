[Back to README](../README.md)

# Development

## Project Structure

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

## Testing

Run the test suite:

```bash
make test
```

Run all quality checks (lint + tests + compile):

```bash
make check
```
