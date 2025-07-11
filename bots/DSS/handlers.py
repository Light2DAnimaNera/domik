import telebot
from telebot import types
from .bot import ds_bot

from shared.env import DSS_FORUM_ID
from shared.models import (
    add_user_if_not_exists,
    get_dss_topic,
    set_dss_topic,
    get_user_by_topic,
)

def register_handlers(bot: telebot.TeleBot) -> None:
    _reply_map: dict[int, tuple[int, int]] = {}

    def ensure_topic(user: types.User) -> tuple[int, bool]:
        """Return topic id for user and flag whether it was created."""
        topic_id = get_dss_topic(user.id)
        created = False
        if topic_id is None:
            name_parts = [user.first_name]
            if user.last_name:
                name_parts.append(user.last_name)
            topic_name = " ".join(name_parts) + f" \u2022 {user.id}"
            topic = bot.create_forum_topic(
                DSS_FORUM_ID,
                name=topic_name,
            )
            topic_id = topic.message_thread_id
            passport_lines = [f"Имя: {' '.join(name_parts)}"]
            if user.username:
                passport_lines.append(f"@{user.username}")
            passport_lines.append(f"ID: {user.id}")
            bot.send_message(DSS_FORUM_ID, "\n".join(passport_lines), message_thread_id=topic_id)
            set_dss_topic(user.id, topic_id)
            created = True
        return topic_id, created
    @bot.message_handler(commands=["start"])
    def cmd_start(message: types.Message) -> None:
        bot.send_message(
            message.chat.id,
            (
                "👤 ДОБРО ПОЖАЛОВАТЬ\n"
                "Пожалуйста, опишите проблему или вопрос. Менеджер свяжется с вами в ближайшее время."
            ),
        )

    @bot.message_handler(func=lambda m: m.chat.type == "private")
    def forward_to_forum(message: types.Message) -> None:
        if message.content_type == "text" and message.text.startswith("/start"):
            return
        add_user_if_not_exists(message)
        topic_id, created = ensure_topic(message.from_user)
        text = message.text or ""
        name_parts = [message.from_user.first_name]
        if message.from_user.last_name:
            name_parts.append(message.from_user.last_name)
        full_name = " ".join(name_parts)
        formatted = f"[{full_name}] пишет:\n{text}"
        msg = bot.send_message(
            DSS_FORUM_ID,
            formatted,
            message_thread_id=topic_id,
        )
        _reply_map[msg.message_id] = (message.chat.id, message.id)

    @bot.message_handler(func=lambda m: m.chat.id == DSS_FORUM_ID and m.message_thread_id)
    def relay_operator(message: types.Message) -> None:
        if message.from_user and message.from_user.is_bot:
            return
        user_id = get_user_by_topic(message.message_thread_id)
        if not user_id:
            return
        if message.reply_to_message and message.reply_to_message.id in _reply_map:
            chat_id, reply_id = _reply_map[message.reply_to_message.id]
            ds_bot.copy_message(
                chat_id,
                message.chat.id,
                message.id,
                reply_to_message_id=reply_id,
            )
        else:
            ds_bot.copy_message(user_id, message.chat.id, message.id)

