import telebot
from telebot import types

from shared.env import DSS_FORUM_ID
from shared.models import (
    add_user_if_not_exists,
    get_dss_topic,
    set_dss_topic,
    get_user_by_topic,
)


def register_handlers(bot: telebot.TeleBot) -> None:
    @bot.message_handler(commands=["start"])
    def cmd_start(message: types.Message) -> None:
        bot.send_message(message.chat.id, "Привет, что интересует?")

    @bot.message_handler(func=lambda m: m.chat.type == "private")
    def forward_to_forum(message: types.Message) -> None:
        if message.content_type == "text" and message.text.startswith("/start"):
            return
        add_user_if_not_exists(message)
        topic_id = get_dss_topic(message.from_user.id)
        if topic_id is None:
            topic = bot.create_forum_topic(
                DSS_FORUM_ID,
                name=f"{message.from_user.first_name} {message.from_user.id}",
            )
            topic_id = topic.message_thread_id
            set_dss_topic(message.from_user.id, topic_id)
            passport = (
                f"Имя: {message.from_user.first_name}\n"
                f"@{message.from_user.username or ''}\n"
                f"ID: {message.from_user.id}\n"
                f"{message.text or ''}"
            )
            bot.send_message(DSS_FORUM_ID, passport, message_thread_id=topic_id)
        else:
            bot.copy_message(
                DSS_FORUM_ID,
                message.chat.id,
                message.id,
                message_thread_id=topic_id,
            )

    @bot.message_handler(func=lambda m: m.chat.id == DSS_FORUM_ID and m.message_thread_id)
    def relay_operator(message: types.Message) -> None:
        if message.from_user and message.from_user.is_bot:
            return
        user_id = get_user_by_topic(message.message_thread_id)
        if user_id:
            bot.copy_message(user_id, message.chat.id, message.id)
