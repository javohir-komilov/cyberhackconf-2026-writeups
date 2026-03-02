import sqlite3
import os

DATABASE = '/app/runtime/app.db'


def init_db():
    os.makedirs('/app/runtime', exist_ok=True)

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role     TEXT NOT NULL DEFAULT 'user',
            note     TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS secrets (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL
        );
    """)

    # --- Foydalanuvchilar seed ---
    users = [
        (1, 'developer', 'devpass2024', 'dev',
         'Dev eslatma: Kirish kaliti: DEV-8472-ALPHA'),
        (2, 'student',   'student123',  'user',
         'Salom! Men o\'quv portalidan foydalanayapman.'),
        (3, 'admin',     'adm!nS3cur3',  'admin',
         'Administrator hisobi. Maxfiy ma\'lumotlar yo\'q.'),
    ]

    for u in users:
        c.execute(
            "INSERT OR IGNORE INTO users (id, username, password, role, note) VALUES (?,?,?,?,?)",
            u
        )

    # --- Sirlar seed ---
    c.execute(
        "INSERT OR IGNORE INTO secrets (name, value) VALUES (?, ?)",
        ('archive_token', 'ARCHIVE-ACCESS-9921')
    )

    conn.commit()
    conn.close()
    print("[DB] Ma'lumotlar bazasi tayyor.")


if __name__ == '__main__':
    init_db()
