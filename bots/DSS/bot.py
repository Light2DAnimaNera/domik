import telebot
from shared.env import TELEGRAM_TOKEN_BOT3

bot = telebot.TeleBot(TELEGRAM_TOKEN_BOT3)

from .handlers import register_handlers
from .bot_commands import setup_default_commands

setup_default_commands(bot)
register_handlers(bot)

def main() -> None:
    """Start the DSS bot."""
    bot.infinity_polling(logger_level=None)


if __name__ == "__main__":
    main()
