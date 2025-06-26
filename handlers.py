import telebot

from gpt_client import GptClient
from models import add_user_if_not_exists, get_all_users
from env import ADMIN_USERNAME
from session_manager import SessionManager
from message_logger import MessageLogger
from summarizer import make_summary
client = GptClient()

def register_handlers(bot: telebot.TeleBot) -> None:
    @bot.message_handler(commands=["start"])
    def cmd_start(message: telebot.types.Message) -> None:
        add_user_if_not_exists(message)
        first_name = message.from_user.first_name
        bot.send_message(
            message.chat.id,
            f"Добро пожаловать, {first_name}",
        )

    @bot.message_handler(commands=["all_users"])
    def cmd_all_users(message: telebot.types.Message) -> None:
        if message.from_user.username != ADMIN_USERNAME:
            return
        users = get_all_users()
        lines = ["Пользователи:"]
        for username, date_joined in users:
            lines.append(f"- @{username} — {date_joined}")
        bot.send_message(message.chat.id, "\n".join(lines))

    @bot.message_handler(commands=["begin"])
    def cmd_begin(message: telebot.types.Message) -> None:
        SessionManager.start(message.from_user)
        bot.send_message(message.chat.id, "Сессия начата.")

    @bot.message_handler(commands=["end"])
    def cmd_end(message: telebot.types.Message) -> None:
        row = SessionManager.active(message.from_user.id)
        if not row:
            bot.send_message(message.chat.id, "Нет активной сессии.")
            return
        summary = make_summary(row["id"])
        SessionManager.close(message.from_user.id, summary)
        bot.send_message(message.chat.id, "Сессия завершена.")

    @bot.message_handler(content_types=["text"])
    def text_handler(message: telebot.types.Message) -> None:
        if message.text.startswith("/"):
            return
        sid = SessionManager.ensure(message.from_user)
        MessageLogger.log(sid, "user", message.text)
        context = MessageLogger.context(sid)
        answer = client.ask(context, message.text)
        MessageLogger.log(sid, "assistant", answer)
        bot.send_message(message.chat.id, answer)
