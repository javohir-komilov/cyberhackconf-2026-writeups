from __future__ import annotations

from datetime import datetime, timezone

from flask import Flask, abort, flash, redirect, render_template, request, url_for
from jinja2 import TemplateError
from jinja2.sandbox import SandboxedEnvironment

from config import JOB_HMAC_SECRET
from db import get_db
from web_helpers import valid_report_key

ssti_env = SandboxedEnvironment(autoescape=False)


def register_reporting_routes(app: Flask) -> None:
    @app.get("/reports")
    def reports() -> str:
        rows = get_db().execute(
            "SELECT id, name, created_at FROM reports ORDER BY id"
        ).fetchall()
        return render_template("reports.html", reports=rows)

    @app.get("/report/<int:report_id>")
    def report_detail(report_id: int) -> str:
        conn = get_db()
        key = request.args.get("key", "")

        report = conn.execute(
            "SELECT id, name, body, created_at FROM reports WHERE id=?",
            (report_id,),
        ).fetchone()
        if report is None:
            abort(404)

        return render_template(
            "report_detail.html",
            report=report,
            key=key,
            can_manage=valid_report_key(report_id, key),
        )

    @app.post("/report/<int:report_id>/template")
    def update_report_template(report_id: int):
        key = request.args.get("key", "")
        if not valid_report_key(report_id, key):
            abort(403)

        body = request.form.get("body", "").strip()
        if not body:
            flash("Template cannot be empty.", "error")
            return redirect(url_for("report_detail", report_id=report_id, key=key))

        conn = get_db()
        conn.execute(
            "UPDATE reports SET body=? WHERE id=?",
            (body, report_id),
        )
        conn.commit()

        flash("Template updated.", "success")
        return redirect(url_for("report_detail", report_id=report_id, key=key))

    @app.get("/report/<int:report_id>/preview")
    def preview_report(report_id: int):
        key = request.args.get("key", "")
        if not valid_report_key(report_id, key):
            abort(403)

        conn = get_db()
        report = conn.execute(
            "SELECT id, name, body FROM reports WHERE id=?",
            (report_id,),
        ).fetchone()
        if report is None:
            abort(404)

        metrics = {
            "open": conn.execute("SELECT COUNT(*) AS c FROM tickets WHERE status='open'").fetchone()["c"],
            "triage": conn.execute("SELECT COUNT(*) AS c FROM tickets WHERE status='triage'").fetchone()["c"],
            "closed": conn.execute("SELECT COUNT(*) AS c FROM tickets WHERE status='closed'").fetchone()["c"],
        }

        context = {
            "report": {
                "id": report["id"],
                "name": report["name"],
                "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            },
            "metrics": metrics,
            "note": "Digest generated from the live helpdesk queue.",
            "integrations": {
                "exports": {
                    "mode": "signed-json",
                    "key": JOB_HMAC_SECRET,
                },
            },
        }

        try:
            rendered = ssti_env.from_string(report["body"]).render(**context)
        except TemplateError as exc:
            rendered = f"<p class='text-rose-300'>Template render error: {exc}</p>"

        return render_template("report_preview.html", report=report, content=rendered)
