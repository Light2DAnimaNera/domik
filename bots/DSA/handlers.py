import telebot
import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from shared.env import ADMIN_USERNAMES

logger = logging.getLogger(__name__)

_admins = [u.lower() for u in ADMIN_USERNAMES]
from shared.reports import format_daily_report
from .newsletter import (
    show_audience_keyboard,
    start_newsletter,
    save_draft,
    clear_draft,
    parse_schedule,
    set_schedule,
    send_now,
    schedule_newsletter,
    AUDIENCE_OPTIONS,
    list_pending_newsletters,
    cancel_newsletter,
    get_newsletter_content,
)


def admin_only(func):
    def wrapper(message: telebot.types.Message) -> None:
        username = (message.from_user.username or "").lower()
        if username not in _admins:
            message.bot.send_message(message.chat.id, "⛔ Доступ запрещен")
            logger.warning("Unauthorized access attempt by @%s", username)
            return
        logger.info("%s invoked %s", username, func.__name__)
        return func(message)

    return wrapper


def register_handlers(bot: telebot.TeleBot) -> None:
    @bot.message_handler(commands=["start"])
    @admin_only
    def cmd_start(message: telebot.types.Message) -> None:
        logger.info("/start from %s", message.from_user.username)
        bot.send_message(message.chat.id, "Bot2 says hi")

    @bot.message_handler(commands=["report"])
    @admin_only
    def cmd_report(message: telebot.types.Message) -> None:
        logger.info("/report from %s", message.from_user.username)
        report = format_daily_report(date.today())
        bot.send_message(message.chat.id, report)

    @bot.message_handler(commands=["newsletter"])
    @admin_only
    def cmd_newsletter(message: telebot.types.Message) -> None:
        logger.info("/newsletter from %s", message.from_user.username)
        show_audience_keyboard(bot, message.chat.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("aud_") or c.data in {"draft_ok", "draft_edit", "send_now", "send_later"})
    def newsletter_callbacks(call: telebot.types.CallbackQuery) -> None:
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        if call.data.startswith("aud_"):
            audience = int(call.data.split("_")[1])
            logger.info("Selected audience %s for user %s", audience, call.from_user.username)
            start_newsletter(call.from_user.id, audience)
            option_text = AUDIENCE_OPTIONS[audience - 1]
            bot.send_message(call.message.chat.id, f"выбран вариант {option_text}")
            msg = bot.send_message(call.message.chat.id, "Пришлите пост для рассылки")

            def _draft_reply(post: telebot.types.Message) -> None:
                logger.info("Draft saved from %s", post.from_user.username)
                save_draft(post.from_user.id, post)
                markup = telebot.types.InlineKeyboardMarkup()
                markup.row(
                    telebot.types.InlineKeyboardButton("\u0414\u0430\u043b\u0435\u0435", callback_data="draft_ok"),
                    telebot.types.InlineKeyboardButton("\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c", callback_data="draft_edit"),
                )
                bot.copy_message(post.chat.id, post.chat.id, post.message_id, reply_markup=markup)

            bot.register_next_step_handler(msg, _draft_reply)
            return

        if call.data == "draft_ok":
            logger.info("Draft confirmed by %s", call.from_user.username)
            bot.send_message(call.message.chat.id, "\u0427\u0435\u0440\u043d\u0435\u0432\u0438\u043a \u043f\u0440\u0438\u043d\u044f\u0442")
            markup = telebot.types.InlineKeyboardMarkup()
            markup.row(
                telebot.types.InlineKeyboardButton("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0441\u0435\u0439\u0447\u0430\u0441", callback_data="send_now"),
            )
            markup.row(
                telebot.types.InlineKeyboardButton("\u041e\u0442\u043b\u043e\u0436\u0435\u043d\u043d\u044b\u0439 \u0437\u0430\u043f\u0443\u0441\u043a", callback_data="send_later"),
            )
            bot.send_message(call.message.chat.id, "Когда отправить пост?", reply_markup=markup)
            return
        if call.data == "send_now":
            logger.info("Immediate send requested by %s", call.from_user.username)
            send_now(bot, call.from_user.id)
            bot.send_message(call.message.chat.id,
                             "\u0421\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u044f \u0431\u0443\u0434\u0443\u0442 \u0440\u0430\u0437\u043e\u0441\u043b\u0430\u043d\u044b \u0441\u043e\u0433\u043b\u0430\u0441\u043d\u043e \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u044b\u043c \u043a\u0440\u0438\u0442\u0435\u0440\u0438\u044f\u043c")
            return
        if call.data == "send_later":
            msg = bot.send_message(call.message.chat.id, "Укажите дату и время в формате DD.MM.YYYY HH:MM (МСК)")

            def _schedule_reply(msg2: telebot.types.Message) -> None:
                dt = parse_schedule(msg2.text)
                tz = ZoneInfo("Europe/Moscow")
                if not dt or dt < datetime.now(tz):
                    bot.send_message(msg2.chat.id, "Неверный формат. Попробуйте ещё раз")
                    bot.register_next_step_handler(msg2, _schedule_reply)
                    return
                logger.info("Scheduled newsletter from %s at %s", msg2.from_user.username, dt.isoformat())
                set_schedule(msg2.from_user.id, dt)
                schedule_newsletter(bot, msg2.from_user.id)
                bot.send_message(msg2.chat.id, f"Запланировано на {dt.strftime('%d.%m.%Y %H:%M')}")
                bot.send_message(
                    msg2.chat.id,
                    "\u0421\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u044f \u0431\u0443\u0434\u0443\u0442 \u0440\u0430\u0437\u043e\u0441\u043b\u0430\u043d\u044b \u0441\u043e\u0433\u043b\u0430\u0441\u043d\u043e \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u044b\u043c \u043a\u0440\u0438\u0442\u0435\u0440\u0438\u044f\u043c",
                )

            bot.register_next_step_handler(msg, _schedule_reply)
            return
        else:
            logger.info("Draft editing requested by %s", call.from_user.username)
            clear_draft(call.from_user.id)
            msg = bot.send_message(call.message.chat.id, "Пришлите новый пост")

            def _draft_reply(post: telebot.types.Message) -> None:
                logger.info("Draft updated by %s", post.from_user.username)
                save_draft(post.from_user.id, post)
                markup = telebot.types.InlineKeyboardMarkup()
                markup.row(
                    telebot.types.InlineKeyboardButton("\u0414\u0430\u043b\u0435\u0435", callback_data="draft_ok"),
                    telebot.types.InlineKeyboardButton("\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c", callback_data="draft_edit"),
                )
                bot.copy_message(post.chat.id, post.chat.id, post.message_id, reply_markup=markup)

            bot.register_next_step_handler(msg, _draft_reply)

    @bot.message_handler(commands=["nl_list"])
    @admin_only
    def cmd_nl_list(message: telebot.types.Message) -> None:
        rows = list_pending_newsletters()
        if not rows:
            bot.send_message(message.chat.id, "список пуст")
            return
        lines = []
        for row in rows:
            dt = (row[1] or "").replace("T", " ")
            preview = (row[4] or "").replace("\n", " ")[:30]
            lines.append(f"[{row[0]}] {dt} {row[2]} {row[3]} \u00ab{preview}\u00bb")
        bot.send_message(message.chat.id, "\n".join(lines))

    @bot.message_handler(commands=["nl_cancel"])
    @admin_only
    def cmd_nl_cancel(message: telebot.types.Message) -> None:
        parts = message.text.split()
        if len(parts) < 2 or not parts[1].isdigit():
            msg = bot.send_message(message.chat.id, "Укажите id рассылки")

            def _id_reply(msg2: telebot.types.Message) -> None:
                if msg2.text and msg2.text.isdigit():
                    if cancel_newsletter(int(msg2.text)):
                        bot.send_message(msg2.chat.id, "OK")
                    else:
                        bot.send_message(msg2.chat.id, "ID рассылки указано не верно")
                else:
                    bot.send_message(msg2.chat.id, "Некорректный id")

            bot.register_next_step_handler(msg, _id_reply)
            return
        if cancel_newsletter(int(parts[1])):
            bot.send_message(message.chat.id, "OK")
        else:
            bot.send_message(message.chat.id, "ID рассылки указано не верно")

    @bot.message_handler(commands=["nl_show"])
    @admin_only
    def cmd_nl_show(message: telebot.types.Message) -> None:
        parts = message.text.split()
        if len(parts) < 2 or not parts[1].isdigit():
            msg = bot.send_message(message.chat.id, "Укажите id рассылки")

            def _id_reply(msg2: telebot.types.Message) -> None:
                if msg2.text and msg2.text.isdigit():
                    content = get_newsletter_content(int(msg2.text))
                    if not content:
                        bot.send_message(msg2.chat.id, "не найдено")
                    else:
                        bot.send_message(msg2.chat.id, content, parse_mode="HTML")
                else:
                    bot.send_message(msg2.chat.id, "Некорректный id")

            bot.register_next_step_handler(msg, _id_reply)
            return
        content = get_newsletter_content(int(parts[1]))
        if not content:
            bot.send_message(message.chat.id, "не найдено")
        else:
            bot.send_message(message.chat.id, content, parse_mode="HTML")

