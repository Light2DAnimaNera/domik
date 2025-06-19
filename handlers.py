import telebot

from gpt_client import GptClient


def register_handlers(bot: telebot.TeleBot) -> None:
    @bot.message_handler(commands=["start"])
    def cmd_start(msg: telebot.types.Message) -> None:
        bot.send_message(msg.chat.id, "Привет! Я готов служить.")

    @bot.message_handler(content_types=["text"])
    def text_handler(msg: telebot.types.Message) -> None:
        if msg.text.startswith("/"):
            return
        answer = GptClient().ask_gpt(msg.text)
        bot.send_message(msg.chat.id, answer)
