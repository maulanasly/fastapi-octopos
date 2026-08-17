[Back to README](../README.md)

# Deployment

For production deployment:

1. Change `SECRET_KEY` to a secure random value
2. Update `ADMIN_PASSWORD` to a strong password
3. Set `BACKEND_CORS_ORIGINS` to your frontend domain
4. Use a production database (PostgreSQL recommended)
5. Set `GOOGLE_CLIENT_ID` if using Google Sign-In
## Docker

The backend ships as a container alongside the Postgres service:

```bash
# 1. Secrets (fail_closed refuses defaults in production)
cat > .env <<'ENVEOF'
SECRET_KEY=change-me-to-a-long-random-string
ADMIN_PASSWORD=change-me-to-a-strong-password
ENVEOF

# 2. Build & start postgres + backend
make docker-up            # docker compose up -d --build

# 3. Useful commands
make docker-logs          # follow backend logs
make docker-ps            # service status
make docker-migrate       # run alembic upgrade head inside the container
make docker-shell         # shell into the backend container
make docker-down          # stop the stack
```

The backend entrypoint waits for Postgres, runs `alembic upgrade head`
automatically (idempotent), then starts uvicorn as PID 1.

Compose interpolates from the same `.env` the app reads (`ENVIRONMENT`,
`SECRET_KEY`, `ADMIN_PASSWORD`, `BACKEND_CORS_ORIGINS`,
`SQLALCHEMY_DATABASE_URI`, `DEFAULT_TAX_RATE`, `LOG_LEVEL`). Inside the
compose network the backend reaches Postgres at `postgres:5432` (the
`.env.example` value with `localhost:5433` is for running the app on the
host).

### Volumes

- `octopos_pgdata` -> Postgres data
- `media` -> `/data/media`: uploaded product images (back this volume up;
  it holds the POS catalog photos).

> Note: if the shared `octopos` database was migrated by a newer codebase
> (its `alembic_version` is ahead of this repo's chain), point the backend
> at a matching database via `SQLALCHEMY_DATABASE_URI` in `.env`.
