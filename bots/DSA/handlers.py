import telebot
from datetime import date, datetime
from zoneinfo import ZoneInfo

from shared.env import ADMIN_USERNAMES

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
)


def admin_only(func):
    def wrapper(message: telebot.types.Message) -> None:
        username = (message.from_user.username or "").lower()
        if username not in _admins:
            message.bot.send_message(message.chat.id, "⛔ Доступ запрещен")
            return
        return func(message)

    return wrapper


def register_handlers(bot: telebot.TeleBot) -> None:
    @bot.message_handler(commands=["start"])
    @admin_only
    def cmd_start(message: telebot.types.Message) -> None:
        bot.send_message(message.chat.id, "Bot2 says hi")

    @bot.message_handler(commands=["report"])
    @admin_only
    def cmd_report(message: telebot.types.Message) -> None:
        report = format_daily_report(date.today())
        bot.send_message(message.chat.id, report)

    @bot.message_handler(commands=["newsletter"])
    @admin_only
    def cmd_newsletter(message: telebot.types.Message) -> None:
        msg = show_audience_keyboard(bot, message.chat.id)

        def _audience_reply(answer: telebot.types.Message) -> None:
            if answer.text not in {"1", "2", "3", "4", "5"}:
                bot.send_message(answer.chat.id, "Введите цифру от 1 до 5")
                return
            start_newsletter(answer.from_user.id, int(answer.text))
            msg2 = bot.send_message(answer.chat.id, "Пришлите пост для рассылки")

            def _draft_reply(post: telebot.types.Message) -> None:
                save_draft(post.from_user.id, post)
                markup = telebot.types.InlineKeyboardMarkup()
                markup.row(
                    telebot.types.InlineKeyboardButton("\u0414\u0430\u043b\u0435\u0435", callback_data="draft_ok"),
                    telebot.types.InlineKeyboardButton("\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c", callback_data="draft_edit"),
                )
                bot.copy_message(post.chat.id, post.chat.id, post.message_id, reply_markup=markup)

            bot.register_next_step_handler(msg2, _draft_reply)

        bot.register_next_step_handler(msg, _audience_reply)

    @bot.callback_query_handler(func=lambda c: c.data in {"draft_ok", "draft_edit"})
    def newsletter_callbacks(call: telebot.types.CallbackQuery) -> None:
        bot.answer_callback_query(call.id)
        if call.data == "draft_ok":
            bot.send_message(call.message.chat.id, "\u0427\u0435\u0440\u043d\u043e\u0432\u0438\u043a \u043f\u0440\u0438\u043d\u044f\u0442")
            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.row("\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0441\u0435\u0439\u0447\u0430\u0441")
            markup.row("\u041e\u0442\u043b\u043e\u0436\u0435\u043d\u043d\u044b\u0439 \u0437\u0430\u043f\u0443\u0441\u043a")
            msg = bot.send_message(call.message.chat.id, "Когда отправить пост?", reply_markup=markup)

            def _time_choice(answer: telebot.types.Message) -> None:
                if answer.text == "\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0441\u0435\u0439\u0447\u0430\u0441":
                    send_now(bot, answer.from_user.id)
                    bot.send_message(answer.chat.id, "Сообщение отправлено")
                else:
                    bot.send_message(answer.chat.id, "Укажите дату и время в формате DD.MM.YYYY HH:MM (МСК)")

                    def _schedule_reply(msg2: telebot.types.Message) -> None:
                        dt = parse_schedule(msg2.text)
                        tz = ZoneInfo("Europe/Moscow")
                        if not dt or dt < datetime.now(tz):
                            bot.send_message(msg2.chat.id, "Неверный формат. Попробуйте ещё раз")
                            bot.register_next_step_handler(msg2, _schedule_reply)
                            return
                        set_schedule(msg2.from_user.id, dt)
                        schedule_newsletter(bot, msg2.from_user.id)
                        bot.send_message(msg2.chat.id, f"Запланировано на {dt.strftime('%d.%m.%Y %H:%M')}")

                    bot.register_next_step_handler(answer, _schedule_reply)

            bot.register_next_step_handler(msg, _time_choice)
        else:
            clear_draft(call.from_user.id)
            msg = bot.send_message(call.message.chat.id, "Пришлите новый пост")

            def _draft_reply(post: telebot.types.Message) -> None:
                save_draft(post.from_user.id, post)
                markup = telebot.types.InlineKeyboardMarkup()
                markup.row(
                    telebot.types.InlineKeyboardButton("\u0414\u0430\u043b\u0435\u0435", callback_data="draft_ok"),
                    telebot.types.InlineKeyboardButton("\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c", callback_data="draft_edit"),
                )
                bot.copy_message(post.chat.id, post.chat.id, post.message_id, reply_markup=markup)

            bot.register_next_step_handler(msg, _draft_reply)

