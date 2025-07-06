import threading
import time
from datetime import datetime, date, time as dt_time, timedelta
from zoneinfo import ZoneInfo

import telebot
from shared.env import TELEGRAM_TOKEN_BOT2, DSA_REPORT_CHAT_ID
from shared.reports import format_daily_report
from .bot_commands import setup_default_commands

bot = telebot.TeleBot(TELEGRAM_TOKEN_BOT2)

from .handlers import register_handlers
setup_default_commands(bot)
register_handlers(bot)


def _report_scheduler() -> None:
    if not DSA_REPORT_CHAT_ID:
        return
    chat_id = int(DSA_REPORT_CHAT_ID)
    tz = ZoneInfo("Europe/Moscow")
    while True:
        now = datetime.now(tz)
        target = datetime.combine(now.date(), dt_time(23, 59), tz)
        if now >= target:
            target += timedelta(days=1)
        time.sleep((target - now).total_seconds())
        report = format_daily_report(target.date())
        bot.send_message(chat_id, report)


def main() -> None:
    threading.Thread(target=_report_scheduler, daemon=True).start()
    bot.infinity_polling(logger_level=None)


if __name__ == "__main__":
    main()
