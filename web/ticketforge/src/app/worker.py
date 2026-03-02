from __future__ import annotations

import sqlite3
import subprocess

from redis import Redis
from rq import Connection, Worker

from config import DB_PATH, EXPORTS_DIR, REDIS_URL


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def run_export(profile_id: int, job_row_id: int) -> None:
    conn = _db()
    conn.execute(
        "UPDATE export_jobs SET status=? WHERE id=?",
        ("running", job_row_id),
    )
    conn.commit()

    profile = conn.execute(
        "SELECT archive_name, source_dir FROM export_profiles WHERE id=?",
        (profile_id,),
    ).fetchone()
    if profile is None:
        conn.execute(
            "UPDATE export_jobs SET status=?, error=?, finished_at=datetime('now') WHERE id=?",
            ("failed", "profile not found", job_row_id),
        )
        conn.commit()
        conn.close()
        return

    archive_name = profile["archive_name"]
    source_dir = profile["source_dir"]

    normalized_name = " ".join(archive_name.strip().split())
    target = f"{EXPORTS_DIR}/{normalized_name}.tgz"
    cmd = f"tar -czf {target} -C {source_dir} ."

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=8,
        )
        if result.returncode == 0:
            conn.execute(
                "UPDATE export_jobs SET status=?, output_file=?, error=?, finished_at=datetime('now') WHERE id=?",
                ("done", f"{archive_name}.tgz", None, job_row_id),
            )
        else:
            err = (result.stderr or result.stdout or "tar failed").strip()[:400]
            conn.execute(
                "UPDATE export_jobs SET status=?, error=?, finished_at=datetime('now') WHERE id=?",
                ("failed", err, job_row_id),
            )
    except Exception as exc:
        conn.execute(
            "UPDATE export_jobs SET status=?, error=?, finished_at=datetime('now') WHERE id=?",
            ("failed", str(exc)[:400], job_row_id),
        )

    conn.commit()
    conn.close()


def main() -> None:
    redis_conn = Redis.from_url(REDIS_URL)
    with Connection(redis_conn):
        worker = Worker(["exports"])
        worker.work()


if __name__ == "__main__":
    main()
