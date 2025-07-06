import telebot
from shared.env import TELEGRAM_TOKEN_BOT2

bot = telebot.TeleBot(TELEGRAM_TOKEN_BOT2)

from .handlers import register_handlers
register_handlers(bot)

if __name__ == "__main__":
    bot.infinity_polling(logger_level=None)
