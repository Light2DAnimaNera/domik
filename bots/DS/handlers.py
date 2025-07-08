import telebot
import math
import logging

from shared.gpt_client import GptClient
from shared.models import (
    add_user_if_not_exists,
    set_blocked,
    is_blocked,
    user_exists,
)
from shared.credits import (
    charge_user,
    get_balance,
    get_today_spent,
    InsufficientCreditsError,
)
from shared.session_manager import SessionManager
from shared.message_logger import MessageLogger
from shared.summarizer import make_summary
from .bot_commands import setup_default_commands
from shared.config import CURRENCY_SYMBOL
client = GptClient()

def register_handlers(bot: telebot.TeleBot) -> None:
    @bot.message_handler(commands=["start"])
    def cmd_start(message: telebot.types.Message) -> None:
        exists = user_exists(message.from_user.id)
        add_user_if_not_exists(message)
        if is_blocked(message.from_user.id):
            bot.send_message(message.chat.id, "[SYSTEM] В доступе отказано.")
            return
        if exists:
            bot.send_message(
                message.chat.id,
                f"👋 С ВОЗВРАЩЕНИЕМ  {message.from_user.first_name}",
                reply_markup=telebot.types.ReplyKeyboardRemove(),
            )
            setup_default_commands(
                bot,
                chat_id=message.chat.id,
            )
            return

        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.row("Да", "Нет")
        msg = bot.send_message(message.chat.id, "Вам есть 18 лет?", reply_markup=markup)

        def _age_reply(answer: telebot.types.Message) -> None:
            if answer.text.lower().startswith("д"):
                set_blocked(answer.from_user.id, False)
                bot.send_message(
                    answer.chat.id,
                    (
                        "👋 ДОБРО ПОЖАЛОВАТЬ\n"
                        "Вам предоставлен доступ к ролевому общению с нейро-госпожой DOMINA SUPREMA. На баланс начислено 100 🝣.\n"
                        "Использование сервиса разрешено только лицам 18+.\n"
                        "Передача, публикация или обсуждение порнографических материалов запрещены.\n"
                        "Ответственность за содержание сообщений несёт пользователь.\n"
                        "Для старта — /begin\n"
                        "Справка — /help"
                    ),
                    reply_markup=telebot.types.ReplyKeyboardRemove(),
                )
                setup_default_commands(
                    bot,
                    chat_id=answer.chat.id,
                )
            else:
                set_blocked(answer.from_user.id, True)
                bot.send_message(answer.chat.id, "[SYSTEM] В доступе отказано.", reply_markup=telebot.types.ReplyKeyboardRemove())

        bot.register_next_step_handler(msg, _age_reply)

    @bot.message_handler(commands=["help"])
    def cmd_help(message: telebot.types.Message) -> None:
        bot.send_message(
            message.chat.id,
            "ℹ️ СПРАВОЧНАЯ ИНФОРМАЦИЯ\n"
            "Доступные команды:\n"
            "/start — Начать работу с ботом\n"
            "/begin — Начать сессию\n"
            "/end — Завершить сессию\n"
            "/balance — Показать баланс\n"
            "/recharge — Пополнить баланс\n\n"
            "Для корректной работы используйте команды в чате с ботом.\n"
            "Если возникли вопросы или требуется помощь, обратитесь в поддержку через Telegram: @DominaSupremaSupportBot",
        )


    @bot.message_handler(commands=["balance"])
    def cmd_balance(message: telebot.types.Message) -> None:
        if is_blocked(message.from_user.id):
            bot.send_message(message.chat.id, "[SYSTEM] В доступе отказано.")
            return
        bal = get_balance(message.from_user.id)
        spent = get_today_spent(message.from_user.id)
        bal_rounded = math.ceil(bal * 100) / 100
        spent_rounded = math.ceil(spent * 100) / 100
        bot.send_message(
            message.chat.id,
            f"💰 БАЛАНС\n"
            f"Текущий баланс: {bal_rounded:.2f} {CURRENCY_SYMBOL}. Использовано сегодня: {spent_rounded:.2f} {CURRENCY_SYMBOL}.",
        )

    @bot.message_handler(commands=["recharge"])
    def cmd_recharge(message: telebot.types.Message) -> None:
        if is_blocked(message.from_user.id):
            bot.send_message(message.chat.id, "[SYSTEM] В доступе отказано.")
            return
        bal = get_balance(message.from_user.id)
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(
            telebot.types.InlineKeyboardButton("300 ₽ → 300 🝣", callback_data="recharge_300"),
            telebot.types.InlineKeyboardButton("500 ₽ → 575 🝣", callback_data="recharge_500"),
        )
        markup.row(
            telebot.types.InlineKeyboardButton("1000 ₽ → 1200 🝣", callback_data="recharge_1000"),
            telebot.types.InlineKeyboardButton("2000 ₽ → 2500 🝣", callback_data="recharge_2000"),
        )
        markup.row(
            telebot.types.InlineKeyboardButton("❤️‍🔥5000 ₽ → 7000 🝣❤️‍🔥", callback_data="recharge_5000")
        )
        bot.send_message(
            message.chat.id,
            (
                "💰 ПОПОЛНЕНИЕ СЧЕТА\n"
                f"Текущий баланс: {bal:.2f} {CURRENCY_SYMBOL}\n"
                "Выберите сумму пополнения с помощью кнопок ниже.\n"
                f"1 рубль = 1 {CURRENCY_SYMBOL}.\n"
                f"Чем больше сумма — тем больше бонусных {CURRENCY_SYMBOL} вы получаете!"
            ),
            reply_markup=markup,
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("recharge_"))
    def recharge_amount(call: telebot.types.CallbackQuery) -> None:
        if is_blocked(call.from_user.id):
            bot.answer_callback_query(call.id, "[SYSTEM] В доступе отказано.", show_alert=True)
            return
        amount = int(call.data.split("_")[1])
        bonus_map = {300: 300, 500: 575, 1000: 1200, 2000: 2500, 5000: 7000}
        credits = bonus_map.get(amount, amount)
        try:
            from shared.yookassa_payment import create_payment, add_pending

            payment = create_payment(call.from_user.id, float(amount))
            add_pending(payment.id, call.from_user.id, float(amount), float(credits))
        except Exception as exc:
            logging.exception("Payment error: %s", exc)
            bot.send_message(call.message.chat.id, "Сервис оплаты недоступен")
            return

        link = payment.confirmation.confirmation_url
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(telebot.types.InlineKeyboardButton("перейти к оплате", url=link))
        text = (
            "💰 ОРДЕР НА ОПЛАТУ\n"
            f"{amount} ₽ → {credits} {CURRENCY_SYMBOL}  \n"
            f"Для оплаты перейдите по ссылке: <a href='{link}'>Оплатить</a>\n"
            "или воспользуйтесь кнопкой ниже."
        )
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")
        bot.answer_callback_query(call.id)


    @bot.message_handler(commands=["begin"])
    def cmd_begin(message: telebot.types.Message) -> None:
        if is_blocked(message.from_user.id):
            bot.send_message(message.chat.id, "[SYSTEM] В доступе отказано.")
            return
        if SessionManager.active(message.from_user.id):
            bot.send_message(
                message.chat.id,
                "🛑 СЕССИЯ УЖЕ АКТИВНА\nЗавершите текущую сессию командой /end, затем используйте /begin.",
            )
            return

        session_id = SessionManager.start(message.from_user)
        if not session_id:
            bot.send_message(
                message.chat.id,
                "❗ ОШИБКА СОЗДАНИЯ СЕССИИ\nПодождите и повторите /begin.",
            )
            return

        bot.send_message(
            message.chat.id,
            "▶️ СЕССИЯ НАЧАТА\nDOMINA SUPREMA готова к общению. Завершить — /end.",
        )

    @bot.message_handler(commands=["end"])
    def cmd_end(message: telebot.types.Message) -> None:
        if is_blocked(message.from_user.id):
            bot.send_message(message.chat.id, "[SYSTEM] В доступе отказано.")
            return
        row = SessionManager.active(message.from_user.id)
        if not row:
            bot.send_message(message.chat.id, "⚠️ СЕССИЯ НЕ ЗАПУЩЕНА\nСначала начните сессию командой /begin.")
            return
        SessionManager.mark_closing(message.from_user.id)
        summary, full_text = make_summary(row["id"])
        end_time = SessionManager.close(message.from_user.id, summary)
        print(full_text)
        bot.send_message(message.chat.id, "✅ СЕССИЯ ЗАВЕРШЕНА\nДля новой сессии используйте /begin.")

    @bot.message_handler(content_types=["text"])
    def text_handler(message: telebot.types.Message) -> None:
        if is_blocked(message.from_user.id):
            bot.send_message(message.chat.id, "[SYSTEM] В доступе отказано.")
            return
        if message.text.startswith("/"):
            return
        row = SessionManager.active(message.from_user.id)
        if not row:
            bot.send_message(
                message.chat.id,
                "⚠️ СЕССИЯ НЕ ЗАПУЩЕНА\nНачните сессию командой /begin, чтобы получить ответ.",
            )
            return
        sid = row["id"]
        MessageLogger.log(sid, "user", message.text)
        context = MessageLogger.context(sid)
        summary = SessionManager.session_summary(sid)
        answer, usage = client.ask(context, message.text, summary)
        try:
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            charge_user(message.from_user.id, prompt_tokens, completion_tokens)
        except InsufficientCreditsError:
            bot.send_message(message.chat.id, "🛑 НЕДОСТАТОЧНО СРЕДСТВ\nПополните баланс командой /recharge. Баланс и расход — /balance.")
            return
        MessageLogger.log(sid, "assistant", answer)
        bot.send_message(message.chat.id, answer)

    @bot.message_handler(content_types=[
        "photo",
        "audio",
        "sticker",
        "video",
        "voice",
        "document",
        "animation",
        "contact",
        "location",
        "video_note",
    ])
    def other_content(message: telebot.types.Message) -> None:
        if is_blocked(message.from_user.id):
            bot.send_message(message.chat.id, "[SYSTEM] В доступе отказано.")
            return
        bot.send_message(
            message.chat.id,
            "⚠️ НЕВЕРНЫЙ ФОРМАТ ВВОДА\nОтправьте текстовое сообщение или команду, чтобы получить ответ.",
        )
