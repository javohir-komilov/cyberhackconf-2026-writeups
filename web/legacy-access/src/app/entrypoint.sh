#!/bin/sh
set -e

# Runtime papkasini yaratish
mkdir -p /app/runtime

# Flagni muhit o'zgaruvchisidan olish va fayl sifatida saqlash
# FLAG env var injected by whale (24-char hex suffix); construct full flag
FLAG="CHC{l3g4cy_4cc3ss_${FLAG:-REDACTED}}"
echo "$FLAG" > /app/runtime/flag.txt
echo "[INIT] Flag /app/runtime/flag.txt ga yozildi."

# Ma'lumotlar bazasini ishga tushirish
python /app/db.py

# Gunicorn ni ishga tushirish
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 60 app:app
