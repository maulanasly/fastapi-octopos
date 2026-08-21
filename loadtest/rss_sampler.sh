#!/usr/bin/env bash
# Sample the backend container's RSS (and CPU%) once per second.
#
# Usage: ./loadtest/rss_sampler.sh <output.csv> [container]
# Stop with SIGINT/SIGTERM; prints avg/max RSS to stderr on exit.

set -euo pipefail

OUT="${1:?usage: rss_sampler.sh <output.csv> [container]}"
CONTAINER="${2:-octopos-backend}"

echo "timestamp,rss_mib,cpu_pct" > "$OUT"

stop() {
  if (( SAMPLED > 0 )); then
    AVG=$(awk -v s="$SUM" -v n="$SAMPLED" 'BEGIN {printf "%.1f", s / n}')
    echo "sampler: ${SAMPLED} samples, RSS avg ${AVG} MiB, max ${MAX} MiB" >&2
  fi
  exit 0
}
trap stop INT TERM

SAMPLED=0
SUM=0
MAX=0
while true; do
  LINE=$(docker stats --no-stream --format '{{.MemUsage}}\t{{.CPUPerc}}' "$CONTAINER" 2>/dev/null) || LINE=""
  if [[ -n "$LINE" ]]; then
    RSS_RAW=$(echo "$LINE" | cut -f1 | awk '{print $1}')
    CPU=$(echo "$LINE" | cut -f2 | tr -d '%')
    UNIT=$(echo "$LINE" | cut -f1 | awk '{print $2}')
    case "$UNIT" in
      GiB) RSS=$(awk -v v="$RSS_RAW" 'BEGIN {printf "%.1f", v * 1024}') ;;
      KiB) RSS=$(awk -v v="$RSS_RAW" 'BEGIN {printf "%.1f", v / 1024}') ;;
      *)   RSS="$RSS_RAW" ;; # MiB
    esac
    echo "$(date +%s),${RSS},${CPU}" >> "$OUT"
    SAMPLED=$((SAMPLED + 1))
    SUM=$(awk -v a="$SUM" -v b="$RSS" 'BEGIN {printf "%.1f", a + b}')
    MAX=$(awk -v a="$MAX" -v b="$RSS" 'BEGIN {if (b > a) print b; else print a}')
  fi
  sleep 1
done
