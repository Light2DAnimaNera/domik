import telebot
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from shared.database import get_connection

# хранит состояние рассылки для каждого администратора
_drafts: dict[int, dict] = {}

AUDIENCE_CODES = {
    1: "all",
    2: "buyers",
    3: "low_balance",
    4: "idle",
    5: "no_sessions",
}

AUDIENCE_OPTIONS = [
    "Все пользователи",
    "Покупали хотя бы раз",
    "Баланс < 20 и ни разу не пополняли",
    "Нет новой сессии > 1 дня",
    "Ни одной сессии",
]


def show_audience_keyboard(bot: telebot.TeleBot, chat_id: int) -> telebot.types.Message:
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.row("1", "2")
    markup.row("3", "4")
    markup.row("5")
    text_lines = [f"{i + 1}. «{option}»" for i, option in enumerate(AUDIENCE_OPTIONS)]
    text = "Выберите аудиторию:\n" + "\n".join(text_lines)
    return bot.send_message(chat_id, text, reply_markup=markup)


def start_newsletter(user_id: int, audience: int) -> None:
    """Запомнить выбранную аудиторию."""
    _drafts[user_id] = {"audience": audience}
    conn = get_connection()
    try:
        cursor = conn.cursor()
        now = datetime.now(ZoneInfo("Europe/Moscow")).isoformat()
        cursor.execute(
            """
            INSERT INTO newsletters(audience, status, created_at)
            VALUES(?, 'draft', ?)
            """,
            (AUDIENCE_CODES.get(audience, "all"), now),
        )
        conn.commit()
        _drafts[user_id]["db_id"] = cursor.lastrowid
    finally:
        conn.close()


def save_draft(user_id: int, message: telebot.types.Message) -> None:
    """Сохранить черновик сообщения."""
    _drafts.setdefault(user_id, {})["draft"] = message
    newsletter_id = _drafts[user_id].get("db_id")
    if newsletter_id:
        content = message.html_text or message.text or message.caption or ""
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE newsletters SET content=? WHERE id=?",
                (content, newsletter_id),
            )
            conn.commit()
        finally:
            conn.close()


def get_draft(user_id: int) -> telebot.types.Message | None:
    return _drafts.get(user_id, {}).get("draft")


def clear_draft(user_id: int) -> None:
    if user_id in _drafts:
        newsletter_id = _drafts[user_id].get("db_id")
        if newsletter_id:
            conn = get_connection()
            try:
                conn.execute(
                    "UPDATE newsletters SET status='canceled' WHERE id=?",
                    (newsletter_id,),
                )
                conn.commit()
            finally:
                conn.close()
        _drafts[user_id].pop("draft", None)


def parse_schedule(text: str) -> datetime | None:
    """Parse date and time in DD.MM.YYYY HH:MM format."""
    try:
        dt = datetime.strptime(text, "%d.%m.%Y %H:%M")
        return dt.replace(tzinfo=ZoneInfo("Europe/Moscow"))
    except ValueError:
        return None


def set_schedule(user_id: int, send_time: datetime) -> None:
    data = _drafts.setdefault(user_id, {})
    data["send_time"] = send_time
    newsletter_id = data.get("db_id")
    if newsletter_id:
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE newsletters SET scheduled_at=?, status='scheduled' WHERE id=?",
                (send_time.isoformat(), newsletter_id),
            )
            conn.commit()
        finally:
            conn.close()


def _get_all_user_ids() -> list[int]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM users WHERE blocked=0")
        return [int(row[0]) for row in cursor.fetchall()]
    finally:
        conn.close()


def _send_to_audience(bot: telebot.TeleBot, audience: int, msg: telebot.types.Message) -> None:
    # пока отправляем всем пользователям
    for user_id in _get_all_user_ids():
        try:
            bot.copy_message(user_id, msg.chat.id, msg.message_id)
        except Exception:
            pass


def _send_text_to_audience(bot: telebot.TeleBot, audience: str, text: str) -> None:
    """Отправить текстовую рассылку указанной аудитории."""
    for user_id in _get_all_user_ids():
        try:
            bot.send_message(user_id, text, parse_mode="HTML")
        except Exception:
            pass


def send_now(bot: telebot.TeleBot, user_id: int) -> None:
    data = _drafts.get(user_id)
    if not data or "draft" not in data:
        return
    _send_to_audience(bot, data.get("audience", 1), data["draft"])
    newsletter_id = data.get("db_id")
    if newsletter_id:
        conn = get_connection()
        try:
            now = datetime.now(ZoneInfo("Europe/Moscow")).isoformat()
            conn.execute(
                "UPDATE newsletters SET status='sent', scheduled_at=?, sent_at=? WHERE id=?",
                (now, now, newsletter_id),
            )
            conn.commit()
        finally:
            conn.close()


def schedule_newsletter(bot: telebot.TeleBot, user_id: int) -> None:
    """Завершает работу с черновиком. Отправка произойдет фоновым планировщиком."""
    if user_id in _drafts:
        _drafts.pop(user_id, None)


def _newsletter_scheduler(bot: telebot.TeleBot) -> None:
    tz = ZoneInfo("Europe/Moscow")
    while True:
        now_iso = datetime.now(tz).isoformat()
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, audience, content FROM newsletters
                WHERE status='scheduled' AND scheduled_at<=?
                """,
                (now_iso,),
            )
            rows = cursor.fetchall()
            for newsletter_id, audience, content in rows:
                _send_text_to_audience(bot, audience, content or "")
                cursor.execute(
                    "UPDATE newsletters SET status='sent', sent_at=? WHERE id=?",
                    (datetime.now(tz).isoformat(), newsletter_id),
                )
            conn.commit()
        finally:
            conn.close()
        time.sleep(60)


def start_newsletter_scheduler(bot: telebot.TeleBot) -> None:
    threading.Thread(target=_newsletter_scheduler, args=(bot,), daemon=True).start()
