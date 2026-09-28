#!/usr/bin/env bash
# Run the benchmark for one vendor
# Usage: ./run.sh <vendor> [duration]
set -euo pipefail

VENDOR="${1:?vendor required}"
DURATION="${2:-5m}"
USERS="${USERS:-50}"
SPAWN_RATE="${SPAWN_RATE:-5}"

echo "→ Benchmarking ${VENDOR} for ${DURATION} with ${USERS} users"

mkdir -p "../results"
export BENCH_VENDOR="${VENDOR}"

locust -f locustfile.py \
  --headless \
  --users "${USERS}" \
  --spawn-rate "${SPAWN_RATE}" \
  --run-time "${DURATION}" \
  --csv="../results/${VENDOR}" \
  --only-summary \
  --html="../results/${VENDOR}.html"
