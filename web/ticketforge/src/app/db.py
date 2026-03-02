from __future__ import annotations

import secrets
import sqlite3
from pathlib import Path
from typing import Any

from flask import g

from config import DB_PATH


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = _connect()
    return g.db


def close_db(_: Any = None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def query(sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    conn = get_db()
    return conn.execute(sql, params).fetchall()


def execute(sql: str, params: tuple[Any, ...] = ()) -> None:
    conn = get_db()
    conn.execute(sql, params)
    conn.commit()


def run_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            snippet TEXT NOT NULL,
            body TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            report_api_key TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS export_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL,
            source_dir TEXT NOT NULL,
            archive_name TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS export_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            output_file TEXT,
            error TEXT,
            created_at TEXT NOT NULL,
            finished_at TEXT,
            FOREIGN KEY(profile_id) REFERENCES export_profiles(id)
        );
        """
    )
    conn.commit()


def seed_data(conn: sqlite3.Connection, report_api_key: str, source_dir: Path) -> None:
    ticket_count = conn.execute("SELECT COUNT(*) AS c FROM tickets").fetchone()["c"]
    if ticket_count == 0:
        conn.executemany(
            """
            INSERT INTO tickets (title, snippet, body, status, created_at)
            VALUES (?, ?, ?, ?, datetime('now', ?))
            """,
            [
                (
                    "Printer queue stalls at midnight",
                    "Nightly queue worker may block after backup",
                    "Observed timeout after cron rotation; please investigate queue backpressure.",
                    "open",
                    "-6 day",
                ),
                (
                    "Agent cannot open attachment",
                    "Upload endpoint returns 403 for PDF only",
                    "Likely MIME filter mismatch on reverse proxy.",
                    "open",
                    "-5 day",
                ),
                (
                    "Escalation webhook retries forever",
                    "Webhook service returns 502 on large payload",
                    "Need staged retries and circuit breaker tuning.",
                    "triage",
                    "-4 day",
                ),
                (
                    "Search feels slow in production",
                    "Query path scans too many rows",
                    "Could use tighter limits and better indexing strategy.",
                    "triage",
                    "-3 day",
                ),
                (
                    "Export package missing images",
                    "Asset path normalizer strips nested folders",
                    "Likely bug in tar include list.",
                    "open",
                    "-2 day",
                ),
                (
                    "Agent theme request",
                    "Need modern dashboard colors for Q1",
                    "Design accepted, waiting on deployment window.",
                    "closed",
                    "-2 day",
                ),
                (
                    "Weekly report generation complete",
                    "Background worker produced archive successfully",
                    "Archive stored in exports bucket with retention policy.",
                    "closed",
                    "-1 day",
                ),
                (
                    "SLA digest draft",
                    "Pending approval from operations lead",
                    "Digest uses same renderer as report preview.",
                    "open",
                    "-8 hour",
                ),
            ],
        )

    report_count = conn.execute("SELECT COUNT(*) AS c FROM reports").fetchone()["c"]
    if report_count == 0:
        conn.execute(
            """
            INSERT INTO reports (name, report_api_key, body, created_at)
            VALUES (?, ?, ?, datetime('now'))
            """,
            (
                "Ops Weekly Digest",
                report_api_key,
                """
<section class=\"space-y-4\">
  <header>
    <h2 class=\"text-2xl font-semibold text-slate-100\">{{ report.name }}</h2>
    <p class=\"text-sm text-slate-300\">Generated at {{ report.generated_at }}</p>
  </header>
  <div class=\"grid gap-3 sm:grid-cols-3\">
    <article class=\"rounded-xl border border-cyan-400/30 bg-slate-900/70 p-3\">
      <p class=\"text-xs uppercase tracking-wide text-cyan-300\">Open Tickets</p>
      <p class=\"text-3xl font-bold text-slate-100\">{{ metrics.open }}</p>
    </article>
    <article class=\"rounded-xl border border-cyan-400/30 bg-slate-900/70 p-3\">
      <p class=\"text-xs uppercase tracking-wide text-cyan-300\">Triage</p>
      <p class=\"text-3xl font-bold text-slate-100\">{{ metrics.triage }}</p>
    </article>
    <article class=\"rounded-xl border border-cyan-400/30 bg-slate-900/70 p-3\">
      <p class=\"text-xs uppercase tracking-wide text-cyan-300\">Closed</p>
      <p class=\"text-3xl font-bold text-slate-100\">{{ metrics.closed }}</p>
    </article>
  </div>
  <p class=\"text-sm text-slate-300\">{{ note }}</p>
</section>
                """.strip(),
            ),
        )

    profile_count = conn.execute("SELECT COUNT(*) AS c FROM export_profiles").fetchone()["c"]
    if profile_count == 0:
        profile_id = 1000 + secrets.randbelow(8000)
        conn.execute(
            """
            INSERT INTO export_profiles (id, label, source_dir, archive_name, updated_at)
            VALUES (?, ?, ?, ?, datetime('now'))
            """,
            (
                profile_id,
                "weekly-helpdesk-bundle",
                str(source_dir),
                "weekly_bundle",
            ),
        )

    conn.commit()
