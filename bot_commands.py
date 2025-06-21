import telebot

DEFAULT_COMMANDS = [
    ("start", "Начать работу с ботом"),
    ("all_users", "Список пользователей"),
]


def setup_default_commands(bot: telebot.TeleBot) -> None:
    """Registers default commands with Telegram API."""
    bot.set_my_commands(
        [telebot.types.BotCommand(cmd, desc) for cmd, desc in DEFAULT_COMMANDS]
    )


def build_commands_keyboard() -> telebot.types.ReplyKeyboardMarkup:
    """Builds a keyboard with available bot commands."""
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for cmd, _ in DEFAULT_COMMANDS:
        keyboard.add(f"/{cmd}")
    return keyboard
