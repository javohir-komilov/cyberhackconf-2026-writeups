import os
import sqlite3
from flask import Flask, request, session, redirect, url_for, render_template, g

app = Flask(__name__)
app.secret_key = os.urandom(32)

DATABASE = '/app/runtime/app.db'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ─── Sahifalar ───────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            error = "Foydalanuvchi nomi va parol kiritilishi shart."
        else:
            db = get_db()
            existing = db.execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone()
            if existing:
                error = "Bunday foydalanuvchi allaqachon mavjud."
            else:
                db.execute(
                    "INSERT INTO users (username, password, role, note) VALUES (?, ?, 'user', '')",
                    (username, password)
                )
                db.commit()
                return redirect(url_for('login'))
    return render_template('register.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        ).fetchone()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            error = "Noto'g'ri foydalanuvchi nomi yoki parol."
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    user_id = request.args.get('user_id', session['user_id'])
    db = get_db()
    # IDOR: user_id tekshirilmaydi
    user = db.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if not user:
        return render_template('error.html', message="Foydalanuvchi topilmadi."), 404
    return render_template('dashboard.html', user=user, current_user=session['username'])


# ─── Bosqich 2: Yashirin endpoint + header ───────────────────────────────────

@app.route('/dev-panel')
@login_required
def dev_panel():
    dev_key = request.headers.get('X-DEV-KEY', '')
    if dev_key != 'DEV-8472-ALPHA':
        return render_template('error.html',
            message="Ruxsat yo'q. Ushbu panel faqat ishlab chiquvchilar uchun mo'ljallangan."), 403
    return render_template('dev_panel.html')


# ─── Bosqich 3: SQL Injection ─────────────────────────────────────────────────

@app.route('/internal')
@login_required
def internal():
    debug = request.args.get('debug', '')
    if debug != 'true':
        return render_template('error.html',
            message="Debug rejimi o'chirilgan."), 403

    q = request.args.get('q', '')
    result = None
    sql_error = None

    if q:
        db = get_db()
        try:
            # SQLi zaiflik: parametrlashtirilmagan so'rov
            query = "SELECT * FROM secrets WHERE name = '" + q + "'"
            cur = db.execute(query)
            result = cur.fetchall()
        except Exception as e:
            sql_error = str(e)

    return render_template('internal.html', q=q, result=result, sql_error=sql_error)


# ─── Bosqich 4: Path Traversal ───────────────────────────────────────────────

@app.route('/archive')
@login_required
def archive():
    token = request.args.get('token', '')
    file_param = request.args.get('file', '')

    if token != 'ARCHIVE-ACCESS-9921':
        return render_template('error.html',
            message="Noto'g'ri token. Arxivga kirish taqiqlangan."), 403

    if not file_param:
        return render_template('archive.html', content=None, filename=None)

    base_dir = '/app/runtime'
    # Path traversal zaiflik: yo'l tekshirilmaydi
    filepath = os.path.join(base_dir, file_param)

    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        return render_template('error.html',
            message=f"Fayl topilmadi: {file_param}"), 404
    except Exception as e:
        return render_template('error.html',
            message=f"Xatolik: {str(e)}"), 500

    return render_template('archive.html', content=content, filename=file_param)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
