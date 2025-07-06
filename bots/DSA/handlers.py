import telebot
from datetime import date

from shared.reports import format_daily_report


def register_handlers(bot: telebot.TeleBot) -> None:
    @bot.message_handler(commands=["start"])
    def cmd_start(message: telebot.types.Message) -> None:
        bot.send_message(message.chat.id, "Bot2 says hi")

    @bot.message_handler(commands=["report"])
    def cmd_report(message: telebot.types.Message) -> None:
        report = format_daily_report(date.today())
        bot.send_message(message.chat.id, report)
