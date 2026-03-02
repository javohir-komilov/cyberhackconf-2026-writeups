from __future__ import annotations

import os
import secrets
import sqlite3
from pathlib import Path

from config import DATA_DIR, DB_PATH, EXPORTS_DIR
from db import run_schema, seed_data

EXPORT_SRC_DIR = DATA_DIR / "exportsrc" / "default_bundle"


def ensure_fs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_SRC_DIR.mkdir(parents=True, exist_ok=True)

    readme = EXPORT_SRC_DIR / "README.txt"
    if not readme.exists():
        readme.write_text(
            "Weekly export source directory for TicketForge.\n",
            encoding="utf-8",
        )

    changelog = EXPORT_SRC_DIR / "changelog.md"
    if not changelog.exists():
        changelog.write_text(
            "# Export Notes\n\n- Packaging ticket snapshots\n- Retention: 14 days\n",
            encoding="utf-8",
        )


def init_database() -> None:
    ensure_fs()

    report_key = os.getenv("REPORT_API_KEY") or secrets.token_hex(16)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    run_schema(conn)
    seed_data(conn, report_key, EXPORT_SRC_DIR)

    conn.execute("UPDATE reports SET report_api_key=? WHERE id=1", (report_key,))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_database()
