from __future__ import annotations

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from db import get_db
from web_helpers import get_active_profile, valid_any_report_key


def register_profile_routes(app: Flask) -> None:
    @app.get("/profile")
    def profile_detail() -> str:
        conn = get_db()
        key = request.args.get("key", "")

        try:
            profile = get_active_profile()
        except LookupError:
            abort(500)

        jobs = conn.execute(
            """
            SELECT id, status, output_file, created_at, finished_at
            FROM export_jobs
            WHERE profile_id=?
            ORDER BY id DESC
            LIMIT 10
            """,
            (profile["id"],),
        ).fetchall()

        return render_template(
            "profile_detail.html",
            profile=profile,
            jobs=jobs,
            key=key,
            can_manage=valid_any_report_key(key),
        )

    @app.post("/profile")
    def update_profile():
        key = request.args.get("key", "")
        if not valid_any_report_key(key):
            abort(403)

        try:
            profile = get_active_profile()
        except LookupError:
            abort(500)

        archive_name = request.form.get("archive_name", "").strip()
        if not archive_name:
            flash("Archive name cannot be empty.", "error")
            return redirect(url_for("profile_detail", key=key))

        conn = get_db()
        conn.execute(
            "UPDATE export_profiles SET archive_name=?, updated_at=datetime('now') WHERE id=?",
            (archive_name, profile["id"]),
        )
        conn.commit()

        flash("Export profile updated.", "success")
        return redirect(url_for("profile_detail", key=key))
