from __future__ import annotations

from flask import Flask, render_template, send_from_directory

from config import EXPORTS_DIR
from db import get_db


def register_exports_routes(app: Flask) -> None:
    @app.get("/exports")
    def exports() -> str:
        files = sorted(
            [
                p.name
                for p in EXPORTS_DIR.glob("*")
                if p.is_file()
            ],
            reverse=True,
        )

        jobs = get_db().execute(
            "SELECT id, profile_id, status, output_file, created_at, finished_at FROM export_jobs ORDER BY id DESC LIMIT 25"
        ).fetchall()

        return render_template("exports.html", files=files, jobs=jobs)

    @app.get("/exports/<path:filename>")
    def export_file(filename: str):
        return send_from_directory(EXPORTS_DIR, filename, as_attachment=True)

    @app.get("/healthz")
    def healthz() -> tuple[str, int]:
        return "ok", 200
