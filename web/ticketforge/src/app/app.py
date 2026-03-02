from __future__ import annotations

import os

from flask import Flask

from db import close_db
from init_db import init_database
from routes.dashboard import register_dashboard_routes
from routes.exports import register_exports_routes
from routes.internal import register_internal_routes
from routes.profile import register_profile_routes
from routes.reporting import register_reporting_routes


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SESSION_SECRET", "ticketforge-session-secret")

    init_database()
    app.teardown_appcontext(close_db)

    register_dashboard_routes(app)
    register_reporting_routes(app)
    register_profile_routes(app)
    register_internal_routes(app)
    register_exports_routes(app)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
