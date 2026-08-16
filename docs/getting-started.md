[Back to README](../README.md)

# Getting Started

## Prerequisites

- Python 3.10+
- Make (optional, for convenience commands)

## 1. Clone repository

```bash
git clone https://github.com/maulanasly/fastapi-octopos.git
cd fastapi-octopos
```

## 2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

## 3. Install dependencies

```bash
make install
```

## 4. Configure environment

Copy `.env.example` and update the values as needed:

```bash
cp .env.example .env
```

## 5. Run migrations

The schema is managed exclusively by Alembic (the app no longer auto-creates tables at startup).

```bash
make migrate
```

> **Upgrading a database created before the migration squash:** the migration history was compacted into a single `0001_initial_schema` migration. Stamp existing databases with `alembic stamp 0001` after confirming their schema matches the current models (or re-run `alembic upgrade head` on a fresh database).

## 6. Run the app

```bash
make run
```

Open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- Admin: `http://127.0.0.1:8000/admin`