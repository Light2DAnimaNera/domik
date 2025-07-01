import telebot

from gpt_client import GptClient
from models import add_user_if_not_exists, get_all_users
from credits import (
    charge_user,
    get_balance,
    get_today_spent,
    get_token_coeff,
    set_token_coeff,
    InsufficientCreditsError,
)
from env import ADMIN_USERNAME
from session_manager import SessionManager
from message_logger import MessageLogger
from summarizer import make_summary
from bot_commands import setup_default_commands
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
        setup_default_commands(
            bot,
            chat_id=message.chat.id,
            username=message.from_user.username,
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

    @bot.message_handler(commands=["balance"])
    def cmd_balance(message: telebot.types.Message) -> None:
        bal = get_balance(message.from_user.id)
        spent = get_today_spent(message.from_user.id)
        bot.send_message(
            message.chat.id,
            f"\U0001F4B3 Баланс: {bal:.4f} \u20A1\nИспользовано сегодня: {spent:.4f} \u20A1",
        )

    @bot.message_handler(commands=["coeff"])
    def cmd_coeff(message: telebot.types.Message) -> None:
        if message.from_user.username != ADMIN_USERNAME:
            return
        coeff = get_token_coeff()
        bot.send_message(message.chat.id, f"Текущий коэффициент: {coeff}")

    @bot.message_handler(commands=["set_coeff"])
    def cmd_set_coeff(message: telebot.types.Message) -> None:
        if message.from_user.username != ADMIN_USERNAME:
            return
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "Использование: /set_coeff <value>")
            return
        try:
            val = float(parts[1])
            set_token_coeff(val)
        except ValueError:
            bot.send_message(message.chat.id, "Некорректное значение")
            return
        bot.send_message(message.chat.id, f"Коэффициент обновлён: {val}")

    @bot.message_handler(commands=["begin"])
    def cmd_begin(message: telebot.types.Message) -> None:
        if SessionManager.active(message.from_user.id):
            bot.send_message(
                message.chat.id,
                "Что бы начать новую сессию, заверши предыдущую сессию",
            )
            return

        session_id = SessionManager.start(message.from_user)
        if not session_id:
            bot.send_message(message.chat.id, "Не удалось начать сессию.")
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
        end_time = SessionManager.close(message.from_user.id, summary)
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
        answer, usage = client.ask(context, message.text, summary)
        try:
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            charge_user(message.from_user.id, prompt_tokens, completion_tokens)
        except InsufficientCreditsError:
            bot.send_message(message.chat.id, "Недостаточно средств. Пополните счёт")
            return
        MessageLogger.log(sid, "assistant", answer)
        bot.send_message(message.chat.id, answer)
