[Back to README](../README.md)

# Deployment

For production deployment:

1. Change `SECRET_KEY` to a secure random value
2. Update `ADMIN_PASSWORD` to a strong password
3. Set `BACKEND_CORS_ORIGINS` to your frontend domain
4. Use a production database (PostgreSQL recommended)
5. Set `GOOGLE_CLIENT_ID` if using Google Sign-In

## Bare metal (Debian 13 VPS, no Docker) — recommended for production

The `deploy/` directory contains everything to run the API natively on a
Tencent (or any Debian 12/13) VPS: PostgreSQL 16 + pgvector, Redis, nginx,
and granian under systemd. Python is the distro's system Python **3.13** —
the same version CI and the Docker image use; keep them in sync when
bumping.

### One-time server setup

```bash
# on the VPS, as root:
DOMAIN=api.example.com ./deploy/bootstrap.sh
```

`bootstrap.sh` installs packages (PGDG repo provides postgresql-16 +
pgvector), creates the `octopos` DB role/database with the `vector`
extension, generates `/etc/octopos/octopos.env` with random secrets,
installs the systemd unit and nginx site, and prints the generated admin
password.

### Release layout

| Path | Purpose |
|---|---|
| `/opt/octopos/releases/<ts>/` | uploaded code, one per deploy |
| `/opt/octopos/current` | symlink to the live release |
| `/opt/octopos/venv` | shared virtualenv (system Python 3.13) |
| `/etc/octopos/octopos.env` | config read by systemd (`EnvironmentFile`) |
| `/var/lib/octopos/media` | uploaded product images (back this up) |

### Continuous deployment

`.github/workflows/cd.yml` triggers on `v*` tags (and manual dispatch):
compile smoke check → `git archive` payload → rsync over SSH → remote
`deploy/deploy.sh <ts>` (pip sync from TUNA mirror, `alembic upgrade head`,
service restart, readiness probe at `/api/v1/health/ready`, automatic
rollback to the previous release if the probe fails). The last 5 releases
are kept; older ones are pruned.

Required GitHub secrets:

| Secret | Value |
|---|---|
| `DEPLOY_SSH_HOST` | VPS IP or hostname |
| `DEPLOY_SSH_USER` | SSH user with sudo rights for `/opt/octopos` |
| `DEPLOY_SSH_KEY` | private key of that user (public half goes in its `authorized_keys`) |
| `DEPLOY_DOMAIN` | optional — enables the public HTTPS health-check step |

The VPS never needs to reach github.com or pypi.org directly: code arrives
via rsync, dependencies come from the TUNA PyPI mirror.

### TLS

After DNS points at the VPS (mainland China: ports 80/443 require ICP
filing for the domain):

```bash
certbot --nginx -d api.example.com
```

### Manual operations

```bash
sudo -u octopos /opt/octopos/bin/rollback.sh   # re-point current + restart
journalctl -u octopos-api -f                   # follow logs
systemctl status octopos-api
```

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
automatically (idempotent), then starts granian (default; `SERVER=uvicorn`
switches) as PID 1.

Postgres runs the `pgvector/pgvector:pg16` image (PostgreSQL 16 with the
`vector` extension — required by migration 0015; plain `postgres:16` will
fail). Enable embeddings with the `EMBEDDING_PROVIDER`/`EMBEDDING_*`
variables; the default `hash` provider works offline.

Compose interpolates from the same `.env` the app reads (`ENVIRONMENT`,
`SECRET_KEY`, `ADMIN_PASSWORD`, `BACKEND_CORS_ORIGINS`,
`SQLALCHEMY_DATABASE_URI`, `DEFAULT_TAX_RATE`, `LOG_LEVEL`, `EMBEDDING_*`). Inside the
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
