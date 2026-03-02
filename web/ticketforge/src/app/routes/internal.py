from __future__ import annotations

from flask import Flask, jsonify, request

from web_helpers import process_signed_export


def register_internal_routes(app: Flask) -> None:
    @app.post("/internal/export")
    def internal_export():
        raw = request.get_data(cache=False)
        signature = request.headers.get("X-Signature", "")

        try:
            job_id = process_signed_export(raw, signature)
        except PermissionError:
            return jsonify({"error": "forbidden"}), 403
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        return jsonify({"queued": True, "job_id": job_id})
