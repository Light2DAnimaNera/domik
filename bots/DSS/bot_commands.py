import telebot


def setup_default_commands(bot: telebot.TeleBot) -> None:
    bot.set_my_commands(
        [
            telebot.types.BotCommand("start", "Запуск"),
            telebot.types.BotCommand("nl_list", "Список рассылок"),
            telebot.types.BotCommand("nl_cancel", "Отменить рассылку"),
            telebot.types.BotCommand("nl_show", "Показать рассылку"),
        ]
    )
