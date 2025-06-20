import telebot

DEFAULT_COMMANDS = [
    ("start", "Начать работу с ботом"),
    ("all_users", "Список пользователей"),
    ("begin", "Начать сессию"),
    ("end", "Завершить сессию"),
]


def setup_default_commands(bot: telebot.TeleBot) -> None:
    """Registers default commands with Telegram API."""
    bot.set_my_commands(
        [telebot.types.BotCommand(cmd, desc) for cmd, desc in DEFAULT_COMMANDS]
    )
