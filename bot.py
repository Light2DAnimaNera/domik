import telebot
import signal
import threading
import time

from env import TELEGRAM_TOKEN
from handlers import register_handlers
from bot_commands import setup_default_commands
from session_manager import SessionManager
from middlewares_error import ErrorMiddleware
from middlewares_activity import ActivityMiddleware

bot = telebot.TeleBot(TELEGRAM_TOKEN, use_class_middlewares=True)
bot.setup_middleware(ErrorMiddleware())
bot.setup_middleware(ActivityMiddleware())
setup_default_commands(bot)
register_handlers(bot)


def _session_monitor() -> None:
    while True:
        SessionManager.expire_idle(bot, 60)
        time.sleep(5)

def _stop_bot(*_: object) -> None:
    """Gracefully stop polling and worker pool."""
    bot.stop_bot()


def main() -> None:
    signal.signal(signal.SIGINT, _stop_bot)
    signal.signal(signal.SIGTERM, _stop_bot)
    threading.Thread(target=_session_monitor, daemon=True).start()
    try:
        bot.infinity_polling(logger_level=None)
    except KeyboardInterrupt:
        _stop_bot()


if __name__ == "__main__":
    main()
