"""
CTF Challenge — H4CK3R_Z0N3
Vulnerabilities: SQL Injection (login) + SSTI (report engine)
"""

import sqlite3
import hashlib
import os

from flask import (
    Flask, request, session,
    redirect, url_for,
    render_template, render_template_string, abort
)

# ──────────────────────────────────────────────
#  App Setup
# ──────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_PATH   = "users.db"
FLAG_PATH = "flag.txt"


# ──────────────────────────────────────────────
#  Database
# ──────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY,
            username TEXT    NOT NULL,
            password TEXT    NOT NULL,
            role     TEXT    DEFAULT 'user'
        )
    """)
    # admin password: s3cur3_p4ssw0rd_never_gonna_guess  (md5)
    admin_hash = hashlib.md5(b"s3cur3_p4ssw0rd_never_gonna_guess").hexdigest()
    guest_hash = hashlib.md5(b"guest123").hexdigest()
    c.execute("INSERT OR IGNORE INTO users VALUES (1, 'admin', ?, 'admin')", (admin_hash,))
    c.execute("INSERT OR IGNORE INTO users VALUES (2, 'guest', ?, 'user')",  (guest_hash,))
    conn.commit()
    conn.close()


def query_user(username: str, password: str):
    """
    ⚠️  INTENTIONALLY VULNERABLE — SQL Injection
    Bypass: username = admin' --
    """
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    sql  = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    try:
        c.execute(sql)
        row = c.fetchone()
    except Exception:
        row = None
    conn.close()
    return row


# ──────────────────────────────────────────────
#  Auth Helper
# ──────────────────────────────────────────────
def admin_required():
    """Return True if the current session is an authenticated admin."""
    return session.get("logged_in") is True and session.get("role") == "admin"


# ──────────────────────────────────────────────
#  Security: block /flag* outside the app
# ──────────────────────────────────────────────
@app.before_request
def block_direct_flag_access():
    path = request.path.lower()
    # Block any URL that contains "flag" unless it's inside /dashboard
    if "flag" in path and not path.startswith("/dashboard"):
        abort(404)


# ──────────────────────────────────────────────
#  Public Routes
# ──────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # Already logged in → redirect to dashboard
    if admin_required():
        return redirect(url_for("dashboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user     = query_user(username, password)

        if user:
            session["logged_in"] = True
            session["username"]  = user[1]
            session["role"]      = user[3]
            if user[3] == "admin":
                return redirect(url_for("dashboard"))
            error = "Access denied. Admins only."
        else:
            error = "Invalid credentials."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ──────────────────────────────────────────────
#  Admin Routes  (session-protected)
# ──────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    if not admin_required():
        abort(403)
    return render_template("dashboard.html", username=session["username"])


@app.route("/dashboard/report", methods=["GET", "POST"])
def report():
    """
    ⚠️  INTENTIONALLY VULNERABLE — SSTI
    render_template_string() receives raw user input.
    Payload: {{config.__class__.__init__.__globals__['os'].popen('cat flag.txt').read()}}
    """
    if not admin_required():
        abort(403)

    output     = None
    prev_query = ""

    if request.method == "POST":
        prev_query = request.form.get("query", "")
        try:
            output = render_template_string(prev_query)
        except Exception as e:
            output = f"Template error: {e}"

    return render_template("report.html", output=output, prev_query=prev_query)


# ──────────────────────────────────────────────
#  Hard-blocked paths
# ──────────────────────────────────────────────
@app.route("/flag.txt")
@app.route("/flag")
def no_flag():
    abort(404)


# ──────────────────────────────────────────────
#  Error Handlers
# ──────────────────────────────────────────────
@app.errorhandler(403)
def err_403(e):
    return render_template("403.html"), 403


@app.errorhandler(404)
def err_404(e):
    return render_template("404.html"), 404


# ──────────────────────────────────────────────
#  Entry Point
# ──────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(debug=False, host="0.0.0.0", port=8000)