import telebot


def register_handlers(bot: telebot.TeleBot) -> None:
    @bot.message_handler(commands=["start"])
    def cmd_start(message: telebot.types.Message) -> None:
        bot.send_message(message.chat.id, "Bot2 says hi")
