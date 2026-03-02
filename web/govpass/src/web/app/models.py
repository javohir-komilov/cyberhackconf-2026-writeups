from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)
    role = db.Column(db.String(16), nullable=False, default="citizen")
    # roles: citizen | researcher | admin

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)


class Application(db.Model):
    __tablename__ = "applications"
    id = db.Column(db.Integer, primary_key=True)
    ref_number = db.Column(db.String(256), unique=True, nullable=False)
    applicant_name = db.Column(db.String(128), nullable=False)
    app_type = db.Column(db.String(32), nullable=False)  # passport | permit | visa
    status = db.Column(db.String(32), nullable=False, default="pending")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Report(db.Model):
    __tablename__ = "reports"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text, nullable=False)
    poc_url = db.Column(db.String(512), nullable=False)
    severity = db.Column(db.String(16), nullable=False, default="medium")
    status = db.Column(db.String(16), nullable=False, default="pending")
    # status: pending | visited | closed
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
