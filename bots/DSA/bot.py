import threading
import time
from datetime import datetime, date, time as dt_time, timedelta
from zoneinfo import ZoneInfo

import logging
import telebot
from shared.env import TELEGRAM_TOKEN_BOT2, DSA_REPORT_CHAT_IDS
from shared.reports import format_daily_report
from .bot_commands import setup_default_commands

logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TELEGRAM_TOKEN_BOT2)

from .handlers import register_handlers
setup_default_commands(bot)
register_handlers(bot)


def _report_scheduler() -> None:
    if not DSA_REPORT_CHAT_IDS:
        logger.info("Report scheduler not started: no chat IDs configured")
        return
    chat_ids = DSA_REPORT_CHAT_IDS
    logger.info("Report scheduler started for chats: %s", chat_ids)
    tz = ZoneInfo("Europe/Moscow")
    while True:
        now = datetime.now(tz)
        target = datetime.combine(now.date(), dt_time(23, 59), tz)
        if now >= target:
            target += timedelta(days=1)
        time.sleep((target - now).total_seconds())
        report = format_daily_report(target.date())
        for chat_id in chat_ids:
            logger.info("Sending daily report to chat %s", chat_id)
            bot.send_message(chat_id, report)


def main() -> None:
    logger.info("DSA bot starting")
    threading.Thread(target=_report_scheduler, daemon=True).start()
    bot.infinity_polling(logger_level=None)


if __name__ == "__main__":
    main()
