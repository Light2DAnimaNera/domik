import sqlite3

from .database import get_connection
from .gpt_client import GptClient

client = GptClient()


def make_summary(session_id: int, previous_summary: str = "") -> tuple[str, str]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content, created FROM messages WHERE session_id=? ORDER BY id",
            (session_id,),
        )
        rows = cursor.fetchall()
        full_text = "\n".join(
            f"[{row[2]}] {row[0]}: {row[1]}" for row in rows
        )
    except sqlite3.Error:
        conn.close()
        return "", ""
    conn.close()
    try:
        summary = client.make_summary(previous_summary, full_text)
    except Exception:
        summary = ""
    return summary, full_text
