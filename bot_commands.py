import telebot
from typing import Iterable, Tuple

from env import ADMIN_USERNAME


DEFAULT_COMMANDS: list[Tuple[str, str]] = [
    ("start", "Начать работу с ботом"),
    ("begin", "Начать сессию"),
    ("end", "Завершить сессию"),
    ("balance", "Показать баланс"),
    ("coeff", "Показать коэффициент"),
]

ADMIN_COMMANDS: list[Tuple[str, str]] = [
    ("all_users", "Список пользователей"),
    ("set_coeff", "Изменить тариф"),
]


def _commands_for_user(username: str | None) -> Iterable[Tuple[str, str]]:
    """Return a command list depending on username."""
    commands = list(DEFAULT_COMMANDS)
    if username == ADMIN_USERNAME:
        commands.extend(ADMIN_COMMANDS)
    return commands


def setup_default_commands(
    bot: telebot.TeleBot,
    *,
    chat_id: int | None = None,
    username: str | None = None,
) -> None:
    """Registers commands for a specific chat or globally."""

    commands = _commands_for_user(username)
    bot.set_my_commands(
        [telebot.types.BotCommand(cmd, desc) for cmd, desc in commands],
        scope=telebot.types.BotCommandScopeChat(chat_id) if chat_id else None,
    )
