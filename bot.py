import telebot

from env import TELEGRAM_TOKEN
from handlers import register_handlers

bot = telebot.TeleBot(TELEGRAM_TOKEN)
register_handlers(bot)

if __name__ == "__main__":
    bot.infinity_polling()
