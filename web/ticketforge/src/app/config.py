import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PUBLIC_DIR = BASE_DIR / "public"
EXPORTS_DIR = PUBLIC_DIR / "exports"
DB_PATH = DATA_DIR / "app.db"

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "5000"))
JOB_HMAC_SECRET = os.environ["JOB_HMAC_SECRET"]
