import telebot
from datetime import date

from shared.env import ADMIN_USERNAMES

_admins = [u.lower() for u in ADMIN_USERNAMES]
from shared.reports import format_daily_report


def admin_only(func):
    def wrapper(message: telebot.types.Message) -> None:
        username = (message.from_user.username or "").lower()
        if username not in _admins:
            message.bot.send_message(message.chat.id, "⛔ Доступ запрещен")
            return
        return func(message)

    return wrapper


def register_handlers(bot: telebot.TeleBot) -> None:
    @bot.message_handler(commands=["start"])
    @admin_only
    def cmd_start(message: telebot.types.Message) -> None:
        bot.send_message(message.chat.id, "Bot2 says hi")

    @bot.message_handler(commands=["report"])
    @admin_only
    def cmd_report(message: telebot.types.Message) -> None:
        report = format_daily_report(date.today())
        bot.send_message(message.chat.id, report)
