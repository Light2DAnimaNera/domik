from telebot.handler_backends import BaseMiddleware
from telebot.types import Message

from .session_manager import SessionManager


class ActivityMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.update_sensitive = False
        self.update_types = ['message']

    def pre_process(self, message: Message, data):
        if SessionManager.active(message.from_user.id):
            SessionManager.update_activity(message.from_user.id)

    def post_process(self, message: Message, data, exception):
        pass

