import sqlite3
from .config import DSS_DB_PATH


def init_dss_db() -> None:
    conn = None
    try:
        conn = sqlite3.connect(DSS_DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS topics (
                user_id INTEGER PRIMARY KEY,
                topic_id INTEGER UNIQUE,
                passport_message_id INTEGER
            )
        """
        )
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_topic_id ON topics(topic_id)"
        )
        cursor.execute("PRAGMA table_info(topics)")
        cols = [r[1] for r in cursor.fetchall()]
        if "passport_message_id" not in cols:
            cursor.execute(
                "ALTER TABLE topics ADD COLUMN passport_message_id INTEGER"
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
