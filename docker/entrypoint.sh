#!/bin/sh
# Container entrypoint: wait for the database, apply migrations, then run
# the app as PID 1 so signals (docker stop) reach uvicorn.
set -e

DB_URL="${SQLALCHEMY_DATABASE_URI:-}"

if [ -n "$DB_URL" ]; then
  echo "[entrypoint] waiting for the database..."
  # Derive host/port from the URL (postgresql+psycopg://user:pass@host:port/db)
  HOST_PORT=$(printf '%s' "$DB_URL" | sed -E 's#^[^@]*@([^/]+)/.*#\1#')
  HOST=$(printf '%s' "$HOST_PORT" | cut -d: -f1)
  PORT=$(printf '%s' "$HOST_PORT" | cut -d: -f2)
  [ -z "$PORT" ] && PORT=5432

  n=0
  while [ "$n" -lt 30 ]; do
    if python -c "import socket,sys; s=socket.socket(); s.settimeout(2); s.connect((sys.argv[1], int(sys.argv[2])))" "$HOST" "$PORT" 2>/dev/null; then
      break
    fi
    echo "[entrypoint] db not ready (attempt $n/30)..."
    n=$((n + 1))
    sleep 2
  done

  if [ "$n" -ge 30 ]; then
    echo "[entrypoint] WARNING: database not reachable; still starting (uvicorn will fail fast if needed)."
  else
    echo "[entrypoint] applying migrations..."
    alembic upgrade head
  fi
fi

echo "[entrypoint] starting uvicorn..."
if [ "${UVICORN_RELOAD:-0}" = "1" ]; then
  # Dev mode: watch the mounted source for changes (no restart needed).
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
