import sqlite3

from config import DB_PATH

def init_db() -> None:
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                date_joined TEXT,
                credits DECIMAL(16,4) NOT NULL DEFAULT 0,
                updated_at TEXT,
                blocked INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        cursor.execute("PRAGMA table_info(users)")
        cols = [r[1] for r in cursor.fetchall()]
        if "credits" not in cols:
            cursor.execute(
                "ALTER TABLE users ADD COLUMN credits DECIMAL(16,4) NOT NULL DEFAULT 0"
            )
        if "updated_at" not in cols:
            cursor.execute("ALTER TABLE users ADD COLUMN updated_at TEXT")
        if "blocked" not in cols:
            cursor.execute(
                "ALTER TABLE users ADD COLUMN blocked INTEGER NOT NULL DEFAULT 0"
            )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                idx INTEGER,
                date_start TEXT,
                date_end TEXT,
                summary TEXT,
                active INTEGER DEFAULT 1
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                role TEXT,
                content TEXT,
                created TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recharge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount DECIMAL(16,4),
                source TEXT,
                timestamp TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pending_payments (
                payment_id TEXT PRIMARY KEY,
                user_id INTEGER,
                amount DECIMAL(16,4),
                credits DECIMAL(16,4)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_daily (
                user_id INTEGER,
                date TEXT,
                spent DECIMAL(16,4),
                PRIMARY KEY(user_id, date)
            )
            """
        )
        cursor.execute(
            "INSERT OR IGNORE INTO settings(key, value) VALUES('token_cost_coeff', '1.0')"
        )
        conn.commit()
    except sqlite3.Error:
        pass
    finally:
        if conn:
            conn.close()


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH, check_same_thread=False)


init_db()
