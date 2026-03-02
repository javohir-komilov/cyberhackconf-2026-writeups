from flask import Blueprint, session, redirect, url_for, render_template, request, flash
from functools import wraps
from ..models import Application, Report, User
from .. import db

portal_bp = Blueprint("portal", __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def researcher_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        if session.get("role") not in ("researcher", "admin"):
            return render_template("errors/403.html"), 403
        return f(*args, **kwargs)
    return decorated


@portal_bp.route("/")
def index():
    return render_template("index.html")


@portal_bp.route("/dashboard")
@login_required
def dashboard():
    apps = Application.query.filter_by(user_id=session["user_id"]).all()
    return render_template("portal/dashboard.html", applications=apps)


@portal_bp.route("/apply", methods=["GET", "POST"])
@login_required
def apply():
    if request.method == "POST":
        import uuid
        app_type = request.form.get("app_type", "passport")
        name = request.form.get("applicant_name", "").strip()
        if not name:
            flash("Applicant name is required.", "danger")
            return render_template("portal/apply.html")
        prefix = {"passport": "PP", "visa": "VZ", "permit": "WP"}.get(app_type, "XX")
        ref = f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
        application = Application(
            ref_number=ref,
            applicant_name=name,
            app_type=app_type,
            status="pending",
            user_id=session["user_id"],
        )
        db.session.add(application)
        db.session.commit()
        flash(f"Application submitted. Reference: {ref}", "success")
        return redirect(url_for("portal.dashboard"))
    return render_template("portal/apply.html")


@portal_bp.route("/report", methods=["GET", "POST"])
@researcher_required
def report():
    """Researchers submit vulnerability disclosure reports here."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        poc_url = request.form.get("poc_url", "").strip()
        severity = request.form.get("severity", "medium")

        if not title or not description or not poc_url:
            flash("All fields are required.", "danger")
            return render_template("portal/report.html")

        r = Report(
            title=title,
            description=description,
            poc_url=poc_url,
            severity=severity,
            status="pending",
            user_id=session["user_id"],
        )
        db.session.add(r)
        db.session.commit()
        flash("Report submitted. Our security team will review it shortly.", "success")
        return redirect(url_for("portal.dashboard"))

    return render_template("portal/report.html")
