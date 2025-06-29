import sqlite3

from database import get_connection
from gpt_client import GptClient

client = GptClient()


def make_summary(session_id: int) -> str:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content FROM messages WHERE session_id=? ORDER BY id",
            (session_id,),
        )
        rows = cursor.fetchall()
        full_text = "\n".join(f"{row[0]}: {row[1]}" for row in rows)
    except sqlite3.Error:
        conn.close()
        return ""
    conn.close()
    try:
        return client.make_summary(full_text)
    except Exception:
        return ""
