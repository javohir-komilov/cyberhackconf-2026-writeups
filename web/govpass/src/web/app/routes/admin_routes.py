from flask import Blueprint, session, redirect, url_for, render_template, request, make_response
from functools import wraps
from ..models import Application, Report, User
from .. import db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    total_apps = Application.query.count()
    pending = Application.query.filter_by(status="pending").count()
    reports = Report.query.filter_by(status="pending").count()
    return render_template(
        "admin/dashboard.html",
        total_apps=total_apps,
        pending=pending,
        pending_reports=reports,
    )


@admin_bp.route("/reports")
@admin_required
def reports():
    all_reports = Report.query.order_by(Report.created_at.desc()).all()
    users = {u.id: u.username for u in User.query.all()}
    return render_template("admin/reports.html", reports=all_reports, users=users)


@admin_bp.route("/tickets")
@admin_required
def tickets():
    """
    Application reference search.
    Results are rendered inside a <frameset> — one <frame> per matching record.
    Deliberately omits X-Frame-Options to allow embedding.
    """
    ref = request.args.get("ref", "")
    if ref:
        # Escape LIKE special characters so the prefix is matched literally
        ref_esc = ref.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        matches = Application.query.filter(
            Application.ref_number.like(f"{ref_esc}%", escape="\\")
        ).all()
    else:
        matches = Application.query.all()

    resp = make_response(render_template("admin/tickets.html", applications=matches, ref=ref))
    # Note: no X-Frame-Options header — admin panel is embeddable by design
    return resp


@admin_bp.route("/ticket/<int:app_id>")
@admin_required
def ticket(app_id):
    app = Application.query.get_or_404(app_id)
    return render_template("admin/ticket.html", application=app)


# Internal API used by the bot
@admin_bp.route("/api/reports/pending")
@admin_required
def api_pending_reports():
    rows = Report.query.filter_by(status="pending").all()
    return [
        {"id": r.id, "poc_url": r.poc_url, "title": r.title}
        for r in rows
    ]


@admin_bp.route("/api/reports/<int:report_id>/visited", methods=["POST"])
@admin_required
def api_mark_visited(report_id):
    r = Report.query.get_or_404(report_id)
    r.status = "visited"
    db.session.commit()
    return {"status": "ok"}
