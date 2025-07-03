import telebot
import math

from gpt_client import GptClient
from models import (
    add_user_if_not_exists,
    get_all_users,
    set_blocked,
    is_blocked,
    user_exists,
)
from credits import (
    charge_user,
    get_balance,
    get_today_spent,
    get_token_coeff,
    set_token_coeff,
    InsufficientCreditsError,
)
from env import ADMIN_USERNAME
from session_manager import SessionManager
from message_logger import MessageLogger
from summarizer import make_summary
from bot_commands import setup_default_commands
from config import CURRENCY_SYMBOL
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
                "[SYSTEM] ДОБРО ПОЖАЛОВАТЬ",
                reply_markup=telebot.types.ReplyKeyboardRemove(),
            )
            setup_default_commands(
                bot,
                chat_id=message.chat.id,
                username=message.from_user.username,
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
                        f"[SYSTEM] ДОБРО ПОЖАЛОВАТЬ ▌ПОЛЬЗОВАТЕЛЬ {answer.from_user.first_name} ЗАРЕГИСТРИРОВАН\n\n"
                        "Вам предоставлен доступ к ролевому общению в формате сессий с нейро-госпожой DOMINA SUPREMA.\n\n"
                        "Использование сервиса разрешено только лицам старше 18 лет.\n"
                        "Передача, публикация или обсуждение порнографических материалов строго запрещены.\n\n"
                        "Ответственность за содержание сообщений, запросов и взаимодействий полностью несёт пользователь.\n\n"
                        "Для инициации первой сессии используй команду /begin.\n"
                        "Справочная информация доступна по команде /help."
                    ),
                    reply_markup=telebot.types.ReplyKeyboardRemove(),
                )
                setup_default_commands(
                    bot,
                    chat_id=answer.chat.id,
                    username=answer.from_user.username,
                )
            else:
                set_blocked(answer.from_user.id, True)
                bot.send_message(answer.chat.id, "[SYSTEM] В доступе отказано.", reply_markup=telebot.types.ReplyKeyboardRemove())

        bot.register_next_step_handler(msg, _age_reply)

    @bot.message_handler(commands=["all_users"])
    def cmd_all_users(message: telebot.types.Message) -> None:
        if is_blocked(message.from_user.id):
            bot.send_message(message.chat.id, "[SYSTEM] В доступе отказано.")
            return
        if message.from_user.username != ADMIN_USERNAME:
            return
        users = get_all_users()
        lines = ["Пользователи:"]
        for username, date_joined in users:
            lines.append(f"- @{username} — {date_joined}")
        bot.send_message(message.chat.id, "\n".join(lines))

    @bot.message_handler(commands=["balance"])
    def cmd_balance(message: telebot.types.Message) -> None:
        if is_blocked(message.from_user.id):
            bot.send_message(message.chat.id, "[SYSTEM] В доступе отказано.")
            return
        bal = get_balance(message.from_user.id)
        bal_ceil = math.ceil(bal * 100) / 100
        spent = get_today_spent(message.from_user.id)
        spent_ceil = math.ceil(spent * 100) / 100
        bot.send_message(
            message.chat.id,
            f"\U0001F4B3 Баланс: {bal_ceil:.2f} {CURRENCY_SYMBOL}\n"
            f"Использовано сегодня: {spent_ceil:.2f} {CURRENCY_SYMBOL}",
        )

    @bot.message_handler(commands=["coeff"])
    def cmd_coeff(message: telebot.types.Message) -> None:
        if is_blocked(message.from_user.id):
            bot.send_message(message.chat.id, "[SYSTEM] В доступе отказано.")
            return
        if message.from_user.username != ADMIN_USERNAME:
            return
        coeff = get_token_coeff()
        bot.send_message(message.chat.id, f"Текущий коэффициент: {coeff}")

    @bot.message_handler(commands=["set_coeff"])
    def cmd_set_coeff(message: telebot.types.Message) -> None:
        if is_blocked(message.from_user.id):
            bot.send_message(message.chat.id, "[SYSTEM] В доступе отказано.")
            return
        if message.from_user.username != ADMIN_USERNAME:
            return
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "Использование: /set_coeff <value>")
            return
        try:
            val = float(parts[1])
            set_token_coeff(val)
        except ValueError:
            bot.send_message(message.chat.id, "Некорректное значение")
            return
        bot.send_message(message.chat.id, f"Коэффициент обновлён: {val}")

    @bot.message_handler(commands=["begin"])
    def cmd_begin(message: telebot.types.Message) -> None:
        if is_blocked(message.from_user.id):
            bot.send_message(message.chat.id, "[SYSTEM] В доступе отказано.")
            return
        if SessionManager.active(message.from_user.id):
            bot.send_message(
                message.chat.id,
                "Что бы начать новую сессию, заверши предыдущую сессию",
            )
            return

        session_id = SessionManager.start(message.from_user)
        if not session_id:
            bot.send_message(message.chat.id, "Не удалось начать сессию.")
            return

        bot.send_message(message.chat.id, "Сессия начата.")

    @bot.message_handler(commands=["end"])
    def cmd_end(message: telebot.types.Message) -> None:
        if is_blocked(message.from_user.id):
            bot.send_message(message.chat.id, "[SYSTEM] В доступе отказано.")
            return
        row = SessionManager.active(message.from_user.id)
        if not row:
            bot.send_message(message.chat.id, "Нет активной сессии.")
            return
        SessionManager.mark_closing(message.from_user.id)
        summary, full_text = make_summary(row["id"])
        end_time = SessionManager.close(message.from_user.id, summary)
        print(full_text)
        bot.send_message(message.chat.id, "Сессия завершена.")

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
                "Требуется начать сессию командой /begin",
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
            bot.send_message(message.chat.id, "Недостаточно средств. Пополните счёт")
            return
        MessageLogger.log(sid, "assistant", answer)
        bot.send_message(message.chat.id, answer)
