import telebot


def setup_default_commands(bot: telebot.TeleBot) -> None:
    bot.set_my_commands(
        [telebot.types.BotCommand("start", "Запуск")]
    )
