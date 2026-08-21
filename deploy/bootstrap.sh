#!/usr/bin/env bash
# One-time server bootstrap for FastAPI OctoPOS on a Debian 13 (trixie) VPS.
#
# Installs and configures, idempotently:
#   - system packages: python3-venv, rsync, git, curl
#   - PostgreSQL 16 + pgvector (PGDG repo; migration 0015 needs `vector`)
#   - Redis (shared rate-limit storage across granian workers)
#   - nginx + certbot (TLS is requested separately after DNS is set)
#   - `octopos` system user, release layout, database and .env skeleton
#
# Usage (as root or with sudo):
#   DOMAIN=api.example.com ./deploy/bootstrap.sh
#
# DOMAIN is optional; when empty the nginx site serves HTTP on port 80 only.

set -euo pipefail

DOMAIN="${DOMAIN:-}"
APP_USER="octopos"
APP_ROOT="/opt/octopos"
MEDIA_DIR="/var/lib/octopos/media"
CONF_DIR="/etc/octopos"
DB_NAME="octopos"
DB_USER="octopos"

if [[ $EUID -ne 0 ]]; then
  echo "run as root: sudo -E ./deploy/bootstrap.sh" >&2
  exit 1
fi

echo "== base packages =="
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg rsync git \
  python3 python3-venv python3-pip redis-server nginx \
  certbot python3-certbot-nginx

echo "== PostgreSQL 16 + pgvector (PGDG) =="
install -d /usr/share/postgresql-common/pgdg &&
  curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
    -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc
echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt trixie-pgdg main" \
  > /etc/apt/sources.list.d/pgdg.list
apt-get update -qq
apt-get install -y -qq postgresql-16 postgresql-16-pgvector
systemctl enable --now postgresql redis-server nginx

DB_PASSWORD="$(openssl rand -hex 24)"
sudo_db() { sudo -u postgres psql -v ON_ERROR_STOP=1 -qtA "$@"; }
if ! sudo_db -c "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1; then
  sudo_db -c "CREATE ROLE ${DB_USER} LOGIN PASSWORD '${DB_PASSWORD}'"
else
  echo "db role ${DB_USER} exists"
fi
if ! sudo_db -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1; then
  sudo_db -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER}"
  sudo_db -d "${DB_NAME}" -c "CREATE EXTENSION IF NOT EXISTS vector"
else
  echo "db ${DB_NAME} exists (ensuring pgvector)"
  sudo_db -d "${DB_NAME}" -c "CREATE EXTENSION IF NOT EXISTS vector"
fi

echo "== app user and directories =="
id -u "${APP_USER}" >/dev/null 2>&1 || useradd --system --home "${APP_ROOT}" --shell /usr/sbin/nologin "${APP_USER}"
install -d -o "${APP_USER}" -g "${APP_USER}" "${APP_ROOT}/releases" "${APP_ROOT}/shared" "${MEDIA_DIR}"

echo "== env skeleton (${CONF_DIR}/octopos.env) =="
install -d -m 700 -o root -g root "${CONF_DIR}"
if [[ ! -f "${CONF_DIR}/octopos.env" ]]; then
  SECRET="$(openssl rand -hex 32)"
  ADMIN_PASS="$(openssl rand -hex 16)"
  cat > "${CONF_DIR}/octopos.env" <<EOF
# Managed by bootstrap.sh — fill in the TODOs before the first deploy.
ENVIRONMENT=production
SECRET_KEY=${SECRET}
ADMIN_USERNAME=admin
ADMIN_PASSWORD=${ADMIN_PASS}
SQLALCHEMY_DATABASE_URI=postgresql+psycopg://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}
RATE_LIMIT_STORAGE_URI=redis://localhost:6379/0
MEDIA_DIR=${MEDIA_DIR}
BACKEND_CORS_ORIGINS=["https://${DOMAIN:-CHANGE-ME.example.com}"]
WEB_CONCURRENCY=2
LOG_LEVEL=INFO
LOG_JSON=True
EOF
  chmod 600 "${CONF_DIR}/octopos.env"
  echo "generated ${CONF_DIR}/octopos.env (admin password: ${ADMIN_PASS})"
else
  echo "${CONF_DIR}/octopos.env already exists — left untouched"
fi

echo "== systemd unit =="
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
install -m 644 "${SCRIPT_DIR}/octopos-api.service" /etc/systemd/system/octopos-api.service
systemctl daemon-reload
systemctl enable octopos-api.service

echo "== nginx site =="
sed "s/__DOMAIN__/${DOMAIN:-_}/" "${SCRIPT_DIR}/nginx-octopos.conf" \
  > /etc/nginx/sites-available/octopos.conf
ln -sf /etc/nginx/sites-available/octopos.conf /etc/nginx/sites-enabled/octopos.conf
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

cat <<'DONE'

Bootstrap complete. Remaining manual steps:
  1. Edit /etc/octopos/octopos.env (CORS origins, GOOGLE_CLIENT_ID if used).
  2. Add the CI deploy key: mkdir -p ~<deploy-user>/.ssh && paste the public
     key from GitHub secret DEPLOY_SSH_KEY into authorized_keys.
  3. Push a v* tag to run the first deploy (HTTP only until step 4).
  4. After DNS points at this host:
       certbot --nginx -d <domain>
     (mainland China: domain on ports 80/443 requires ICP filing.)
DONE
