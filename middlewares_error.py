from telebot.handler_backends import BaseMiddleware
from telebot.types import Message

from credits import InsufficientCreditsError


class ErrorMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.update_sensitive = False
        self.update_types = ['message']

    def pre_process(self, message: Message, data):
        pass

    def post_process(self, message: Message, data, exception):
        if isinstance(exception, InsufficientCreditsError):
            message.bot.send_message(message.chat.id, 'Недостаточно средств. Пополните счёт')
            return True
        return False
