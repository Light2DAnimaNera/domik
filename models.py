from datetime import datetime
import sqlite3
import telebot

from database import get_connection


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
                INSERT INTO users (telegram_id, username, first_name, date_joined)
                VALUES (?, ?, ?, ?)
                """,
                (telegram_id, username, first_name, date_joined),
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
