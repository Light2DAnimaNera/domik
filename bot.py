import telebot

from env import TELEGRAM_TOKEN
from handlers import register_handlers
from bot_commands import setup_default_commands

bot = telebot.TeleBot(TELEGRAM_TOKEN)
setup_default_commands(bot)
register_handlers(bot)

if __name__ == "__main__":
    bot.infinity_polling()
