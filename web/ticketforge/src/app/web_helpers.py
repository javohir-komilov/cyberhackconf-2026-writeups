from __future__ import annotations

import hashlib
import hmac
import json

import redis
from rq import Queue

from config import JOB_HMAC_SECRET, REDIS_URL
from db import get_db

redis_conn = redis.from_url(REDIS_URL)
export_queue = Queue("exports", connection=redis_conn)


def sign_body(raw: bytes) -> str:
    return hmac.new(JOB_HMAC_SECRET.encode(), raw, hashlib.sha256).hexdigest()


def valid_report_key(report_id: int, key: str) -> bool:
    if not key:
        return False
    row = get_db().execute(
        "SELECT 1 FROM reports WHERE id=? AND report_api_key=?",
        (report_id, key),
    ).fetchone()
    return row is not None


def valid_any_report_key(key: str) -> bool:
    if not key:
        return False
    row = get_db().execute(
        "SELECT 1 FROM reports WHERE report_api_key=?",
        (key,),
    ).fetchone()
    return row is not None


def get_active_profile():
    row = get_db().execute(
        "SELECT id, label, source_dir, archive_name, updated_at FROM export_profiles ORDER BY id LIMIT 1"
    ).fetchone()
    if row is None:
        raise LookupError("missing export profile")
    return row


def enqueue_export(profile_id: int) -> int:
    conn = get_db()
    exists = conn.execute(
        "SELECT id FROM export_profiles WHERE id=?",
        (profile_id,),
    ).fetchone()
    if exists is None:
        raise ValueError("unknown profile")

    cur = conn.execute(
        """
        INSERT INTO export_jobs (profile_id, status, output_file, error, created_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        """,
        (profile_id, "queued", None, None),
    )
    job_row_id = cur.lastrowid
    conn.commit()

    try:
        export_queue.enqueue("worker.run_export", profile_id, job_row_id, job_timeout=20)
    except Exception as exc:
        conn.execute(
            "UPDATE export_jobs SET status=?, error=?, finished_at=datetime('now') WHERE id=?",
            ("failed", f"queue error: {exc}", job_row_id),
        )
        conn.commit()
        raise

    return job_row_id


def process_signed_export(raw: bytes, signature: str) -> int:
    expected = sign_body(raw)
    if not hmac.compare_digest(expected, signature):
        raise PermissionError("invalid signature")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"invalid json: {exc}") from exc

    if "profile_id" not in payload:
        raise ValueError("missing profile_id")

    return enqueue_export(int(payload["profile_id"]))
