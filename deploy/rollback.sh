#!/usr/bin/env bash
# Re-point /opt/octopos/current at the previous release and restart.
# Usage: sudo -u octopos /opt/octopos/bin/rollback.sh  (or via sudo)

set -euo pipefail

APP_ROOT="/opt/octopos"
current="$(readlink "${APP_ROOT}/current")"
previous="$(ls -1dt "${APP_ROOT}"/releases/*/ | grep -v "^${current}/$" | head -1)"

[[ -n "${previous}" ]] || { echo "no previous release to roll back to" >&2; exit 1; }

ln -sfn "${previous%/}" "${APP_ROOT}/current"
systemctl restart octopos-api.service
sleep 3
curl -fsS http://127.0.0.1:8000/api/v1/health/ready \
  && echo "rolled back to ${previous%/}" \
  || { echo "rollback health check failed — inspect journalctl -u octopos-api" >&2; exit 1; }
