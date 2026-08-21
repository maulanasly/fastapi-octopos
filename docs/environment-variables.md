[Back to README](../README.md)

# Environment Variables

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
| `BACKEND_CORS_ORIGIN_REGEX` | Optional regex allowing additional origins (e.g. ephemeral dev-client ports) | empty |
| `SQLALCHEMY_DATABASE_URI` | Database connection string | SQLite file (`sql_app.db`) |
| `SECRET_KEY` | JWT signing secret (change in production) | Hardcoded tutorial key (insecure; production refuses it) |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime in minutes | `11520` (8 days) |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID (optional) | `None` |
| `ADMIN_USERNAME` | Admin panel username | `admin` |
| `ADMIN_PASSWORD` | Admin panel password | `admin` (change in production) |
| `ADMIN_SESSION_HOURS` | Admin panel session lifetime | `12` |
| `ORDER_RESERVATION_TIMEOUT_MINUTES` | Stock reservation expiry | `15` |
| `RESERVATION_AUTO_EXPIRE_ENABLED` | Periodic + startup sweep of expired reservations (required in production when reservations are on) | `False` |
| `RESERVATION_AUTO_EXPIRE_INTERVAL_SECONDS` | Sweep interval | `300` |
| `DEFAULT_TAX_RATE` | Rate for the migration-seeded default tax rule | `0.0` |
| `DEFAULT_TAX_NAME` | Name for the migration-seeded default tax rule | `VAT` |
| `LOGIN_MAX_ATTEMPTS` | Failed logins before temporary lockout | `5` |
| `LOGIN_LOCKOUT_MINUTES` | Lockout duration after repeated failures | `15` |
| `MEDIA_DIR` | Directory for uploaded product images | `media` |
| `REPLENISHMENT_AUTO_PO_ENABLED` | Scheduled auto-generation of draft purchase orders from reorder points | `False` |
| `REPLENISHMENT_CHECK_INTERVAL_SECONDS` | Auto-PO check interval | `3600` |
| `REPLENISHMENT_LOOKBACK_DAYS` | Sales lookback for replenishment velocity | `30` |
| `RATE_LIMIT_STORAGE_URI` | Rate-limit storage for slowapi; empty = in-memory (single process). Set e.g. `redis://localhost:6380` for multi-worker deployments | empty |
| `EMBEDDING_PROVIDER` | Semantic-search embeddings: `hash` (offline default), `api` (OpenAI-compatible), or `none` | `hash` |
| `EMBEDDING_MODEL` | Model name sent to the embedding API | `all-minilm` |
| `EMBEDDING_DIM` | Embedding dimension — must stay `384` (matches the `products.embedding` vector column) | `384` |
| `EMBEDDING_BASE_URL` | Embedding API base URL (OpenAI-compatible `/embeddings`) | empty |
| `EMBEDDING_API_KEY` | Embedding API key | empty |
