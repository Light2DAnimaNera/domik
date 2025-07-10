import telebot
import signal
import threading
import time

from shared.env import (
    TELEGRAM_TOKEN_BOT1 as TELEGRAM_TOKEN,
    TELEGRAM_TOKEN_BOT2,
    DSA_REPORT_CHAT_IDS,
)
from shared.credits import add_credits, get_balance
from shared.models import get_username
from shared.config import CURRENCY_SYMBOL
from shared.yookassa_payment import list_pending, remove_pending, payment_status, log_payment
from .handlers import register_handlers
from .bot_commands import setup_default_commands
from shared.session_manager import SessionManager
from shared.middlewares_error import ErrorMiddleware
from shared.middlewares_activity import ActivityMiddleware
from bots.DSA.newsletter import start_newsletter_scheduler

bot = telebot.TeleBot(TELEGRAM_TOKEN, use_class_middlewares=True, num_threads=30)
bot.setup_middleware(ErrorMiddleware())
bot.setup_middleware(ActivityMiddleware())
setup_default_commands(bot)
register_handlers(bot)

dsa_bot = None
if TELEGRAM_TOKEN_BOT2 and DSA_REPORT_CHAT_IDS:
    dsa_bot = telebot.TeleBot(TELEGRAM_TOKEN_BOT2)


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
                log_payment(payment_id, user_id, amount, status, credits)
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
                if dsa_bot:
                    try:
                        username = get_username(user_id)
                        username = f"@{username}" if username else str(user_id)
                        for chat_id in DSA_REPORT_CHAT_IDS:
                            dsa_bot.send_message(
                                chat_id,
                                (
                                    "НОВОЕ ПОСТУПЛЕНИЕ\n"
                                    f"Пользователь {username} через сервис YooKassa\n"
                                    f"Оплатил подписку на {amount:.2f} ₽"
                                ),
                            )
                    except Exception:
                        pass
            elif status == "canceled":
                print(
                    f"Payment {payment_id} for user {user_id} canceled"
                )
                log_payment(payment_id, user_id, amount, status, 0)
                remove_pending(payment_id)
            else:
                print(
                    f"Payment {payment_id} for user {user_id} pending, status: {status}"
                )
                log_payment(payment_id, user_id, amount, status, 0)
        time.sleep(30)

def _stop_bot(*_: object) -> None:
    """Gracefully stop polling and worker pool."""
    bot.stop_bot()


def main() -> None:
    signal.signal(signal.SIGINT, _stop_bot)
    signal.signal(signal.SIGTERM, _stop_bot)
    threading.Thread(target=_session_monitor, daemon=True).start()
    threading.Thread(target=_payment_monitor, daemon=True).start()
    start_newsletter_scheduler(bot)
    try:
        bot.infinity_polling(logger_level=None)
    except KeyboardInterrupt:
        _stop_bot()


if __name__ == "__main__":
    main()
