import os
import sqlite3

DB_PATH = "users.db"

def init_db() -> None:
    conn = None
    try:
        db_exists = os.path.isfile(DB_PATH)
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        if not db_exists:
            cursor.execute(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,
                    username TEXT,
                    first_name TEXT,
                    date_joined TEXT
                )
                """
            )
        else:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
            )
            if not cursor.fetchone():
                cursor.execute(
                    """
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id INTEGER UNIQUE,
                        username TEXT,
                        first_name TEXT,
                        date_joined TEXT
                    )
                    """
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
