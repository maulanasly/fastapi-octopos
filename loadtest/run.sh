#!/usr/bin/env bash
# Full load-test run: seed -> RSS sampler -> k6 -> combined summary.
#
# Usage:
#   ./loadtest/run.sh [profile]          # profile: dev | prod (default dev)
#   VUS=50 DURATION=2m ./loadtest/run.sh dev

set -euo pipefail

cd "$(dirname "$0")/.."

PROFILE="${1:-${PROFILE:-dev}}"
BASE_URL="${BASE_URL:-http://localhost:8000}"
VUS="${VUS:-50}"
DURATION="${DURATION:-2m}"
CONTAINER="${CONTAINER:-octopos-backend}"
RESULTS="loadtest/results"
K6="${K6:-k6}"

mkdir -p "$RESULTS"

echo "== loadtest profile=${PROFILE} base=${BASE_URL} vus=${VUS} duration=${DURATION} =="

./loadtest/seed.sh

RSS_CSV="${RESULTS}/rss-${PROFILE}.csv"
./loadtest/rss_sampler.sh "$RSS_CSV" "$CONTAINER" &
SAMPLER_PID=$!
trap 'kill "$SAMPLER_PID" 2>/dev/null || true' EXIT

K6_BIN="$K6"
if ! command -v "$K6" >/dev/null 2>&1 && [[ -x "$HOME/.local/bin/k6" ]]; then
  K6_BIN="$HOME/.local/bin/k6"
fi

BASE_URL="$BASE_URL" PROFILE="$PROFILE" VUS="$VUS" DURATION="$DURATION" \
  "$K6_BIN" run loadtest/k6-load.js

kill "$SAMPLER_PID" 2>/dev/null || true
wait "$SAMPLER_PID" 2>/dev/null || true
trap - EXIT

RSS_AVG=$(awk -F, 'NR>1 {s+=$2; n++} END {if (n) printf "%.1f", s/n}' "$RSS_CSV")
RSS_MAX=$(awk -F, 'NR>1 {if ($2 > m) m=$2} END {printf "%.1f", m}' "$RSS_CSV")

echo
echo "== ${PROFILE} results =="
echo "RSS avg: ${RSS_AVG:-n/a} MiB | RSS max: ${RSS_MAX:-n/a} MiB (${SAMPLES_FILE:-$RSS_CSV})"
