import telebot

from gpt_client import GptClient
from models import add_user_if_not_exists, get_all_users
from env import ADMIN_USERNAME
from bot_commands import build_commands_keyboard


def register_handlers(bot: telebot.TeleBot) -> None:
    @bot.message_handler(commands=["start"])
    def cmd_start(message: telebot.types.Message) -> None:
        add_user_if_not_exists(message)
        first_name = message.from_user.first_name
        keyboard = build_commands_keyboard()
        bot.send_message(
            message.chat.id,
            f"Добро пожаловать, {first_name}",
            reply_markup=keyboard,
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

    @bot.message_handler(content_types=["text"])
    def text_handler(message: telebot.types.Message) -> None:
        if message.text.startswith("/"):
            return
        answer = GptClient().ask_gpt(message.text)
        bot.send_message(message.chat.id, answer)
