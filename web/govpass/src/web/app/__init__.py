from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from . import config

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)

    from .routes.auth_routes import auth_bp
    from .routes.portal_routes import portal_bp
    from .routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        _init_db()

    return app


def _init_db():
    from .models import User, Application
    db.create_all()

    # Seed admin account
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", role="admin")
        admin.set_password(config.ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.flush()

        # The flag lives as a classified permit reference — admin-eyes only
        flag_app = Application(
            ref_number=config.FLAG,
            applicant_name="CLASSIFIED",
            app_type="special",
            status="classified",
            user_id=admin.id,
        )
        db.session.add(flag_app)

    # Seed a few decoy applications so the DB looks real
    if Application.query.count() <= 1:
        decoy_user = User.query.filter_by(username="citizen1").first()
        if not decoy_user:
            decoy_user = User(username="citizen1", role="citizen")
            decoy_user.set_password("citizen1")
            db.session.add(decoy_user)
            db.session.flush()

        decoys = [
            Application(ref_number="PP-2024-00142", applicant_name="Alisher Toshmatov",
                        app_type="passport", status="approved", user_id=decoy_user.id),
            Application(ref_number="PP-2024-00198", applicant_name="Dilnoza Yusupova",
                        app_type="passport", status="pending", user_id=decoy_user.id),
            Application(ref_number="VZ-2024-00034", applicant_name="Bobur Karimov",
                        app_type="visa", status="approved", user_id=decoy_user.id),
        ]
        for d in decoys:
            db.session.add(d)

    db.session.commit()
