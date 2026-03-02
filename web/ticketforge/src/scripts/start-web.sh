#!/usr/bin/env bash
set -euo pipefail
umask 0002

mkdir -p /app/data /app/public/exports

if [[ ! -f /app/data/runtime.env ]]; then
  python3 - <<'PY' > /app/data/runtime.env
import secrets
print(f"JOB_HMAC_SECRET={secrets.token_hex(24)}")
print(f"REPORT_API_KEY={secrets.token_hex(16)}")
print(f"FLASK_SESSION_SECRET={secrets.token_hex(24)}")
PY
fi

set -a
source /app/data/runtime.env
set +a

python3 /app/init_db.py
chmod 664 /app/data/runtime.env /app/data/app.db || true
chmod -R g+rwX /app/public/exports /app/data/exportsrc || true

exec gunicorn \
  --bind 0.0.0.0:5000 \
  --workers 2 \
  --threads 4 \
  --timeout 30 \
  app:app
