from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from db import get_db


def register_dashboard_routes(app: Flask) -> None:
    @app.get("/")
    def home() -> str:
        conn = get_db()
        tickets = conn.execute(
            "SELECT id, title, snippet, status, created_at FROM tickets ORDER BY id DESC LIMIT 8"
        ).fetchall()
        report = conn.execute("SELECT id, name FROM reports ORDER BY id LIMIT 1").fetchone()
        jobs = conn.execute(
            "SELECT id, status, output_file, created_at FROM export_jobs ORDER BY id DESC LIMIT 6"
        ).fetchall()

        metrics = {
            "open": conn.execute("SELECT COUNT(*) AS c FROM tickets WHERE status='open'").fetchone()["c"],
            "triage": conn.execute("SELECT COUNT(*) AS c FROM tickets WHERE status='triage'").fetchone()["c"],
            "closed": conn.execute("SELECT COUNT(*) AS c FROM tickets WHERE status='closed'").fetchone()["c"],
        }

        return render_template(
            "index.html",
            tickets=tickets,
            report=report,
            jobs=jobs,
            metrics=metrics,
        )

    @app.get("/search")
    def search() -> tuple[object, int] | object:
        q = request.args.get("q", "").strip()
        if not q:
            return jsonify([])

        needle = q.replace("%", "")
        sql = (
            "SELECT id, title, snippet FROM tickets "
            f"WHERE title LIKE '%{needle}%' OR snippet LIKE '%{needle}%' "
            "ORDER BY id DESC LIMIT 20"
        )

        try:
            rows = get_db().execute(sql).fetchall()
        except Exception:
            return jsonify([])

        return jsonify([dict(row) for row in rows])
