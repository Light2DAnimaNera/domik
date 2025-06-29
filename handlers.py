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
        session_id = SessionManager.start(message.from_user)
        if not session_id:
            bot.send_message(
                message.chat.id,
                "Что бы начать новую сессию, заверши предыдущую сессию",
            )
            return
        bot.send_message(message.chat.id, "Сессия начата.")

    @bot.message_handler(commands=["end"])
    def cmd_end(message: telebot.types.Message) -> None:
        row = SessionManager.active(message.from_user.id)
        if not row:
            bot.send_message(message.chat.id, "Нет активной сессии.")
            return
        SessionManager.mark_closing(message.from_user.id)
        summary, full_text = make_summary(row["id"])
        SessionManager.close(message.from_user.id, summary)
        print(full_text)
        bot.send_message(message.chat.id, "Сессия завершена.")

    @bot.message_handler(content_types=["text"])
    def text_handler(message: telebot.types.Message) -> None:
        if message.text.startswith("/"):
            return
        row = SessionManager.active(message.from_user.id)
        if not row:
            bot.send_message(
                message.chat.id,
                "Требуется начать сессию командой /begin",
            )
            return
        sid = row["id"]
        MessageLogger.log(sid, "user", message.text)
        context = MessageLogger.context(sid)
        summary = SessionManager.session_summary(sid)
        answer = client.ask(context, message.text, summary)
        MessageLogger.log(sid, "assistant", answer)
        bot.send_message(message.chat.id, answer)
