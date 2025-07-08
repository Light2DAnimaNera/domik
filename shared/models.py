from datetime import datetime
import sqlite3
import telebot

from .database import get_connection
from .dss_database import get_dss_connection
from .config import INITIAL_CREDITS


def add_user_if_not_exists(message: telebot.types.Message) -> None:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        telegram_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        cursor.execute(
            "SELECT id FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )
        if cursor.fetchone() is None:
            date_joined = datetime.now().date().isoformat()
            cursor.execute(
                """
                INSERT INTO users (telegram_id, username, first_name, date_joined, credits, blocked)
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                (telegram_id, username, first_name, date_joined, INITIAL_CREDITS),
            )
            conn.commit()
    except sqlite3.Error:
        pass
    finally:
        conn.close()


def get_all_users() -> list[tuple]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username, date_joined FROM users ORDER BY id"
        )
        return cursor.fetchall()
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def set_blocked(user_id: int, blocked: bool) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET blocked=? WHERE telegram_id=?",
            (1 if blocked else 0, user_id),
        )
        conn.commit()
    except sqlite3.Error:
        pass
    finally:
        conn.close()


def is_blocked(user_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT blocked FROM users WHERE telegram_id=?", (user_id,))
        row = cursor.fetchone()
        return bool(row[0]) if row else False
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def user_exists(user_id: int) -> bool:
    """Return True if user is already present in the database."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE telegram_id=?", (user_id,))
        return cursor.fetchone() is not None
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def get_username(user_id: int) -> str:
    """Return stored Telegram username for a user."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username FROM users WHERE telegram_id=?",
            (user_id,),
        )
        row = cursor.fetchone()
        return row[0] if row and row[0] else ""
    except sqlite3.Error:
        return ""
    finally:
        conn.close()


_dss_topic_cache: dict[int, int] = {}

def _load_dss_topics() -> None:
    """Preload DSS tickets from the database into memory."""
    conn = get_dss_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, topic_id FROM tickets")
        for user_id, topic_id in cursor.fetchall():
            _dss_topic_cache[int(user_id)] = int(topic_id)
    except sqlite3.Error:
        pass
    finally:
        conn.close()

_load_dss_topics()


def get_dss_topic(user_id: int) -> int | None:
    """Return cached topic id for the user if available."""
    if user_id in _dss_topic_cache:
        return _dss_topic_cache[user_id]
    conn = get_dss_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT topic_id FROM tickets WHERE user_id=?",
            (user_id,),
        )
        row = cursor.fetchone()
        if row:
            _dss_topic_cache[user_id] = int(row[0])
            return int(row[0])
        return None
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def set_dss_topic(user_id: int, topic_id: int) -> None:
    """Store or update mapping between user and topic."""
    conn = get_dss_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO tickets(user_id, topic_id) VALUES(?, ?)",
            (user_id, topic_id),
        )
        conn.commit()
        _dss_topic_cache[user_id] = topic_id
    except sqlite3.Error:
        pass
    finally:
        conn.close()


def get_user_by_topic(topic_id: int) -> int | None:
    """Return user id associated with a forum topic."""
    conn = get_dss_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id FROM tickets WHERE topic_id=?",
            (topic_id,),
        )
        row = cursor.fetchone()
        return int(row[0]) if row else None
    except sqlite3.Error:
        return None
    finally:
        conn.close()


