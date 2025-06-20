import sqlite3
from collections import defaultdict
from datetime import datetime

from config import CONTEXT_LIMIT
from database import get_connection


class MessageLogger:
    def __init__(self) -> None:
        self._cache: defaultdict[int, list[str]] = defaultdict(list)

    def log(self, session_id: int, role: str, content: str) -> None:
        conn = get_connection()
        try:
            conn.execute(
                """
                INSERT INTO messages (session_id, role, content, created)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, role, content, datetime.now().isoformat()),
            )
            conn.commit()
        except sqlite3.Error:
            pass
        finally:
            conn.close()
        self._cache[session_id].append(content)

    def context(self, session_id: int) -> str:
        messages = self._cache[session_id]
        text = "\n".join(messages)
        if len(text) <= CONTEXT_LIMIT:
            return text
        while len(text) > CONTEXT_LIMIT and messages:
            messages.pop(0)
            text = "\n".join(messages)
        return text


MessageLogger = MessageLogger()
