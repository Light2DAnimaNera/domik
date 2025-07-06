import telebot
import signal
import threading
import time

from shared.env import TELEGRAM_TOKEN_BOT1 as TELEGRAM_TOKEN
from shared.credits import add_credits, get_balance
from shared.config import CURRENCY_SYMBOL
from shared.yookassa_payment import list_pending, remove_pending, payment_status, log_payment
from .handlers import register_handlers
from .bot_commands import setup_default_commands
from shared.session_manager import SessionManager
from shared.middlewares_error import ErrorMiddleware
from shared.middlewares_activity import ActivityMiddleware

bot = telebot.TeleBot(TELEGRAM_TOKEN, use_class_middlewares=True, num_threads=10)
bot.setup_middleware(ErrorMiddleware())
bot.setup_middleware(ActivityMiddleware())
setup_default_commands(bot)
register_handlers(bot)


def _session_monitor() -> None:
    while True:
        SessionManager.expire_idle(bot, 600)
        time.sleep(5)


def _payment_monitor() -> None:
    while True:
        for payment_id, user_id, amount, credits in list_pending():
            try:
                status = payment_status(payment_id)
            except Exception:
                continue
            if status == "succeeded":
                print(
                    f"Payment {payment_id} for user {user_id} succeeded, "
                    f"crediting {credits:.0f}"
                )
                add_credits(user_id, credits, "yookassa")
                log_payment(payment_id, user_id, amount, status)
                remove_pending(payment_id)
                bal = get_balance(user_id)
                bot.send_message(
                    user_id,
                    (
                        "✅ ОПЛАТА ПРОШЛА УСПЕШНО\n"
                        f"Ваш баланс пополнен на {credits:.0f} {CURRENCY_SYMBOL}.\n"
                        f"Текущий баланс: {bal:.2f} {CURRENCY_SYMBOL}.\n"
                        "Чтобы продолжить общение, используйте команду /begin."
                    ),
                )
            elif status == "canceled":
                print(
                    f"Payment {payment_id} for user {user_id} canceled"
                )
                log_payment(payment_id, user_id, amount, status)
                remove_pending(payment_id)
            else:
                print(
                    f"Payment {payment_id} for user {user_id} pending, status: {status}"
                )
                log_payment(payment_id, user_id, amount, status)
        time.sleep(30)

def _stop_bot(*_: object) -> None:
    """Gracefully stop polling and worker pool."""
    bot.stop_bot()


def main() -> None:
    signal.signal(signal.SIGINT, _stop_bot)
    signal.signal(signal.SIGTERM, _stop_bot)
    threading.Thread(target=_session_monitor, daemon=True).start()
    threading.Thread(target=_payment_monitor, daemon=True).start()
    try:
        bot.infinity_polling(logger_level=None)
    except KeyboardInterrupt:
        _stop_bot()


if __name__ == "__main__":
    main()
