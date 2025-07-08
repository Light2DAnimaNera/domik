import sqlite3
from .config import DSS_DB_PATH


def init_dss_db() -> None:
    """Create the DSS tickets table if it does not exist."""
    conn = None
    try:
        conn = sqlite3.connect(DSS_DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                user_id INTEGER PRIMARY KEY,
                topic_id INTEGER NOT NULL UNIQUE
            )
            """
        )
        conn.commit()
    except sqlite3.Error:
        pass
    finally:
        if conn:
            conn.close()


def get_dss_connection() -> sqlite3.Connection:
    return sqlite3.connect(DSS_DB_PATH, check_same_thread=False)


init_dss_db()
