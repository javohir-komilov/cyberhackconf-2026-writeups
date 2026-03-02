#!/usr/bin/env bash
set -euo pipefail

mkdir -p /app/data /app/public/exports

for _ in $(seq 1 60); do
  if [[ -f /app/data/runtime.env && -f /app/data/app.db ]]; then
    break
  fi
  sleep 1
done

if [[ ! -f /app/data/runtime.env ]]; then
  echo "runtime env missing"
  exit 1
fi

set -a
source /app/data/runtime.env
set +a

exec python3 /app/worker.py
