import telebot
from telebot import types

from shared.env import DSS_FORUM_ID
from shared.models import (
    add_user_if_not_exists,
    get_dss_topic,
    set_dss_topic,
    get_user_by_topic,
    get_user_by_passport_msg,
)


def register_handlers(bot: telebot.TeleBot) -> None:
    _reply_map: dict[int, tuple[int, int]] = {}

    def ensure_topic(user: types.User, first_text: str | None) -> tuple[int, bool]:
        """Return topic id for user and flag whether it was created."""
        topic_id = get_dss_topic(user.id)
        created = False
        if topic_id is None:
            topic = bot.create_forum_topic(
                DSS_FORUM_ID,
                name=f"{user.first_name} {user.id}",
            )
            topic_id = topic.message_thread_id
            passport = (
                f"Имя: {user.first_name}\n"
                f"@{user.username or ''}\n"
                f"ID: {user.id}\n"
            )
            if first_text:
                passport += first_text
            intro = bot.send_message(DSS_FORUM_ID, passport, message_thread_id=topic_id)
            set_dss_topic(user.id, topic_id, intro.message_id)
            created = True
        return topic_id, created
    @bot.message_handler(commands=["start"])
    def cmd_start(message: types.Message) -> None:
        bot.send_message(message.chat.id, "Привет, что интересует?")

    @bot.message_handler(func=lambda m: m.chat.type == "private")
    def forward_to_forum(message: types.Message) -> None:
        if message.content_type == "text" and message.text.startswith("/start"):
            return
        add_user_if_not_exists(message)
        topic_id, created = ensure_topic(message.from_user, message.text or "")
        if created:
            return
        msg_id = bot.forward_message(
            DSS_FORUM_ID,
            message.chat.id,
            message.id,
            message_thread_id=topic_id,
        )
        _reply_map[msg_id.message_id] = (message.chat.id, message.id)

    @bot.message_handler(func=lambda m: m.chat.id == DSS_FORUM_ID and m.message_thread_id)
    def relay_operator(message: types.Message) -> None:
        if message.from_user and message.from_user.is_bot:
            return
        user_id = get_user_by_topic(message.message_thread_id)
        if not user_id and message.reply_to_message:
            if message.reply_to_message.forward_from:
                user_id = message.reply_to_message.forward_from.id
                set_dss_topic(user_id, message.message_thread_id)
            else:
                user_id = get_user_by_passport_msg(message.reply_to_message.message_id)
        if not user_id:
            return
        if message.reply_to_message and message.reply_to_message.id in _reply_map:
            chat_id, reply_id = _reply_map[message.reply_to_message.id]
            bot.copy_message(
                chat_id,
                message.chat.id,
                message.id,
                reply_to_message_id=reply_id,
            )
        else:
            bot.copy_message(user_id, message.chat.id, message.id)
