import telebot
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from shared.database import get_connection

# хранит состояние рассылки для каждого администратора
_drafts: dict[int, dict] = {}

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


def save_draft(user_id: int, message: telebot.types.Message) -> None:
    """Сохранить черновик сообщения."""
    _drafts.setdefault(user_id, {})["draft"] = message


def get_draft(user_id: int) -> telebot.types.Message | None:
    return _drafts.get(user_id, {}).get("draft")


def clear_draft(user_id: int) -> None:
    if user_id in _drafts:
        _drafts[user_id].pop("draft", None)


def parse_schedule(text: str) -> datetime | None:
    """Parse date and time in DD.MM.YYYY HH:MM format."""
    try:
        dt = datetime.strptime(text, "%d.%m.%Y %H:%M")
        return dt.replace(tzinfo=ZoneInfo("Europe/Moscow"))
    except ValueError:
        return None


def set_schedule(user_id: int, send_time: datetime) -> None:
    _drafts.setdefault(user_id, {})["send_time"] = send_time


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


def send_now(bot: telebot.TeleBot, user_id: int) -> None:
    data = _drafts.get(user_id)
    if not data or "draft" not in data:
        return
    _send_to_audience(bot, data.get("audience", 1), data["draft"])


def schedule_newsletter(bot: telebot.TeleBot, user_id: int) -> None:
    data = _drafts.get(user_id)
    if not data or "draft" not in data or "send_time" not in data:
        return

    def _worker() -> None:
        tz = ZoneInfo("Europe/Moscow")
        delay = (data["send_time"] - datetime.now(tz)).total_seconds()
        if delay > 0:
            time.sleep(delay)
        _send_to_audience(bot, data.get("audience", 1), data["draft"])

    threading.Thread(target=_worker, daemon=True).start()
