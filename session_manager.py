import sqlite3
from datetime import datetime

from config import DB_PATH
from database import get_connection


class SessionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._active = {}
            cls._instance._closing = set()
        return cls._instance

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat()

    def mark_closing(self, user_id: int) -> None:
        """Помечает сессию пользователя как завершающуюся."""
        self._closing.add(user_id)

    def unmark_closing(self, user_id: int) -> None:
        """Снимает пометку о завершающейся сессии."""
        self._closing.discard(user_id)

    def start(self, user) -> int:
        user_id = user.id
        if user_id in self._closing:
            return 0
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT MAX(idx) FROM sessions WHERE telegram_id=?",
                (user_id,),
            )
            row = cursor.fetchone()
            next_idx = (row[0] or 0) + 1
            cursor.execute(
                """
                INSERT INTO sessions (telegram_id, idx, date_start)
                VALUES (?, ?, ?)
                """,
                (user_id, next_idx, self._now()),
            )
            conn.commit()
            session_id = cursor.lastrowid
            self._active[user_id] = session_id
            return session_id
        except sqlite3.Error:
            return 0
        finally:
            conn.close()

    def ensure(self, user) -> int:
        row = self.active(user.id)
        if row:
            return row["id"]
        return self.start(user)

    def close(self, user_id: int, summary: str | None = None) -> None:
        row = self.active(user_id)
        if not row:
            return
        self.unmark_closing(user_id)
        conn = get_connection()
        try:
            conn.execute(
                """
                UPDATE sessions
                SET date_end=?, summary=?, active=0
                WHERE id=?
                """,
                (self._now(), summary, row["id"]),
            )
            conn.commit()
        except sqlite3.Error:
            pass
        finally:
            conn.close()
        self._active.pop(user_id, None)

    def active(self, user_id: int):
        if user_id in self._active:
            session_id = self._active[user_id]
            conn = get_connection()
            try:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM sessions WHERE id=? AND active=1",
                    (session_id,),
                )
                row = cursor.fetchone()
                if row:
                    return row
            except sqlite3.Error:
                return False
            finally:
                conn.close()

        conn = get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM sessions WHERE telegram_id=? AND active=1",
                (user_id,),
            )
            row = cursor.fetchone()
            if row:
                self._active[user_id] = row["id"]
                return row
        except sqlite3.Error:
            return False
        finally:
            conn.close()
        return False


SessionManager = SessionManager()
