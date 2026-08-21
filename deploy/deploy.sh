#!/usr/bin/env bash
# Server-side deploy: activate an rsync'd release, sync deps, migrate, restart.
#
# Layout:
#   /opt/octopos/releases/<ts>   uploaded code (rsync target)
#   /opt/octopos/current         symlink to the live release
#   /opt/octopos/venv            shared virtualenv (system Python 3.13)
#   /etc/octopos/octopos.env     config (EnvironmentFile)
#
# Called by .github/workflows/cd.yml as:
#   /opt/octopos/releases/<ts>/deploy/deploy.sh <ts>
#
# Rollback: /opt/octopos/bin/rollback.sh re-points `current` and restarts.

set -euo pipefail

TS="${1:?usage: deploy.sh <release-timestamp>}"
APP_ROOT="/opt/octopos"
RELEASE_DIR="${APP_ROOT}/releases/${TS}"
VENV="${APP_ROOT}/venv"
HEALTH_URL="http://127.0.0.1:8000/api/v1/health/ready"

[[ -d "${RELEASE_DIR}" ]] || { echo "release ${RELEASE_DIR} missing" >&2; exit 1; }

echo "== deps =="
if [[ ! -x "${VENV}/bin/python" ]]; then
  python3 -m venv "${VENV}"
fi
# TUNA mirror: the VPS should not depend on pypi.org reachability.
"${VENV}/bin/pip" install --upgrade pip -q \
  -i https://pypi.tuna.tsinghua.edu.cn/simple
"${VENV}/bin/pip" install -q -r "${RELEASE_DIR}/requirements.txt" \
  -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "== migrate (${RELEASE_DIR}) =="
cd "${RELEASE_DIR}"
set -a; source /etc/octopos/octopos.env; set +a
"${VENV}/bin/alembic" upgrade head

echo "== switch current -> ${TS} =="
previous="$(readlink -f "${APP_ROOT}/current" || true)"
ln -sfn "${RELEASE_DIR}" "${APP_ROOT}/current"

echo "== restart =="
systemctl restart octopos-api.service

echo "== health check =="
ok=0
for _ in $(seq 1 30); do
  if curl -fsS "${HEALTH_URL}" | grep -q '"database"'; then ok=1; break; fi
  sleep 2
done

if [[ "${ok}" != "1" ]]; then
  echo "health check FAILED — rolling back to ${previous:-<none>}" >&2
  if [[ -n "${previous}" && -d "${previous}" ]]; then
    ln -sfn "${previous}" "${APP_ROOT}/current"
    systemctl restart octopos-api.service
    echo "rolled back to ${previous}" >&2
  else
    echo "no previous release; leaving failed release in place" >&2
  fi
  journalctl -u octopos-api.service -n 50 --no-pager >&2 || true
  exit 1
fi

# Keep the last 5 releases.
cd "${APP_ROOT}/releases" && ls -1dt */ 2>/dev/null | tail -n +6 | while read -r old; do
  rm -rf "${APP_ROOT}/releases/${old}"
done

echo "== deploy ${TS} complete =="
