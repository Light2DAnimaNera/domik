import telebot
from env import TELEGRAM_TOKEN

bot = telebot.TeleBot(TELEGRAM_TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я готов служить.")


if __name__ == "__main__":
    bot.infinity_polling()
