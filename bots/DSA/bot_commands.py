import telebot


def setup_default_commands(bot: telebot.TeleBot) -> None:
    bot.set_my_commands(
        [
            telebot.types.BotCommand("start", "Начать"),
            telebot.types.BotCommand("report", "Отчет за сегодня"),
            telebot.types.BotCommand("coeff", "Показать коэффициент"),
            telebot.types.BotCommand("set_coeff", "Изменить коэффициент"),
            telebot.types.BotCommand("newsletter", "Рассылка"),
            telebot.types.BotCommand("nl_list", "Список рассылок"),
            telebot.types.BotCommand("nl_cancel", "Отменить рассылку <id>"),
            telebot.types.BotCommand("nl_show", "Показать рассылку <id>"),
        ]
    )
