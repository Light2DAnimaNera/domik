import sqlite3
from datetime import datetime, timezone, timedelta
try:
    from zoneinfo import ZoneInfo
    MOSCOW_TZ = ZoneInfo("Europe/Moscow")
except Exception:  # pragma: no cover - fallback for older Python
    MOSCOW_TZ = timezone(timedelta(hours=3), name="MSK")
import time

from .config import DB_PATH
from .database import get_connection


class SessionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._active = {}
            cls._instance._closing = set()
            cls._instance._summaries = {}
            cls._instance._activity = {}
        return cls._instance

    @staticmethod
    def _now() -> str:
        return datetime.now(MOSCOW_TZ).strftime("%m-%d-%y %H-%M")

    @staticmethod
    def _fetch_last_summary(user_id: int) -> str:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT summary FROM sessions
                WHERE telegram_id=? AND active=0 AND summary IS NOT NULL
                ORDER BY id DESC LIMIT 1
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            return row[0] if row else ""
        except sqlite3.Error:
            return ""
        finally:
            conn.close()

    def mark_closing(self, user_id: int) -> None:
        """Помечает сессию пользователя как завершающуюся."""
        self._closing.add(user_id)

    def unmark_closing(self, user_id: int) -> None:
        """Снимает пометку о завершающейся сессии."""
        self._closing.discard(user_id)

    def start(self, user) -> int:
        user_id = user.id
        if user_id in self._closing or self.active(user_id):
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
            self._summaries[session_id] = self._fetch_last_summary(user_id)
            self._activity[user_id] = time.time()
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

    def update_activity(self, user_id: int) -> None:
        """Обновляет время последней активности пользователя."""
        if user_id in self._active:
            self._activity[user_id] = time.time()

    def expire_idle(self, bot, timeout: int) -> None:
        """Закрывает сессии, простаивавшие дольше `timeout` секунд."""
        now = time.time()
        to_close = [uid for uid, ts in self._activity.items() if now - ts > timeout]
        for uid in to_close:
            row = self.active(uid)
            if not row:
                continue
            from .summarizer import make_summary
            prev_summary = self.session_summary(row["id"])
            summary, _ = make_summary(row["id"], prev_summary)
            end_time = self.close(uid, summary)
            try:
                bot.send_message(uid, "⌛ СЕССИЯ ЗАВЕРШЕНА\nПревышено время ожидания ответа. Начните новую сессию командой /begin.")
            except Exception:
                pass

    def close(self, user_id: int, summary: str | None = None) -> str | None:
        row = self.active(user_id)
        if not row:
            return None
        self.unmark_closing(user_id)
        end_time = self._now()
        conn = get_connection()
        try:
            conn.execute(
                """
                UPDATE sessions
                SET date_end=?, summary=?, active=0
                WHERE id=?
                """,
                (end_time, summary, row["id"]),
            )
            conn.commit()
        except sqlite3.Error:
            pass
        finally:
            conn.close()
        session_id = self._active.pop(user_id, None)
        if session_id:
            self._summaries.pop(session_id, None)
        self._activity.pop(user_id, None)
        return end_time

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

    def session_summary(self, session_id: int) -> str:
        return self._summaries.get(session_id, "")


SessionManager = SessionManager()
