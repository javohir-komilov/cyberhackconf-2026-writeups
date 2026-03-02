from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from ..models import User
from .. import db
from ..auth import verify_sso_token

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("portal.dashboard"))
        flash("Invalid credentials.", "danger")
    return render_template("auth/login.html")


@auth_bp.route("/auth/sso", methods=["POST"])
def sso():
    """
    SSO bearer token endpoint.
    Clients POST a signed RS256 JWT; we verify it and establish a session.

    Expected JWT payload fields:
        sub  (str)  – username to register / log in as
        role (str)  – desired role: citizen | researcher
        exp  (int)  – expiry unix timestamp
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return {"error": "Missing Bearer token"}, 401

    token = auth_header[len("Bearer "):]

    try:
        payload = verify_sso_token(token)
    except Exception as exc:
        return {"error": str(exc)}, 401

    sub = payload.get("sub")
    role = payload.get("role", "citizen")

    if not sub:
        return {"error": "Token missing 'sub' claim"}, 400

    # Only citizen and researcher roles may be granted via SSO
    if role not in ("citizen", "researcher"):
        role = "citizen"

    user = User.query.filter_by(username=sub).first()
    if not user:
        user = User(username=sub, role=role)
        db.session.add(user)
        db.session.commit()
    else:
        # Role can be upgraded by SSO token (intentional — SSO is the authority)
        user.role = role
        db.session.commit()

    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role

    return {"status": "ok", "role": user.role}, 200


@auth_bp.route("/auth/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
