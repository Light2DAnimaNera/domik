import telebot
import signal

from env import TELEGRAM_TOKEN
from handlers import register_handlers
from bot_commands import setup_default_commands
from session_manager import SessionManager

bot = telebot.TeleBot(TELEGRAM_TOKEN)
setup_default_commands(bot)
register_handlers(bot)

def _stop_bot(*_: object) -> None:
    """Gracefully stop polling and worker pool."""
    bot.stop_bot()


def main() -> None:
    signal.signal(signal.SIGINT, _stop_bot)
    signal.signal(signal.SIGTERM, _stop_bot)
    try:
        bot.infinity_polling(logger_level=None)
    except KeyboardInterrupt:
        _stop_bot()


if __name__ == "__main__":
    main()
