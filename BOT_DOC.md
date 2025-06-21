# Документация по боту

## Команды бота

- `/start` — приветственное сообщение и вывод меню команд.
- `/all_users` — выводит список всех пользователей. Доступно только администратору.

## Файлы и функции

### `bot.py`
- Создаёт объект `TeleBot`, регистрирует команды и запускает бесконечный polling.

### `bot_commands.py`
- `DEFAULT_COMMANDS` — список команд бота.
- `setup_default_commands(bot)` — регистрирует их в Telegram.
- `build_commands_keyboard()` — возвращает клавиатуру с этими командами.

### `database.py`
- `init_db()` — инициализирует базу данных SQLite и создаёт таблицу `users` при первом запуске.
- `get_connection()` — возвращает соединение с базой данных.

### `gpt_client.py`
- Класс `GptClient` — обёртка над API OpenAI.
  - `__init__()` — создаёт клиента OpenAI с параметрами из переменных окружения.
  - `ask_gpt(user_text)` — отправляет текст пользователя в модель и возвращает ответ.

### `models.py`
- `add_user_if_not_exists(message)` — добавляет пользователя в базу, если его там ещё нет.
- `get_all_users()` — возвращает список всех пользователей.

### `handlers.py`
- Функция `register_handlers(bot)` регистрирует обработчики:
  - `cmd_start(message)` — обрабатывает команду `/start` и отправляет клавиатуру с командами.
  - `cmd_all_users(message)` — обрабатывает команду `/all_users` (только для админа).
  - `text_handler(message)` — отвечает на обычные текстовые сообщения через `GptClient`.

### `env.py`
- Загружает переменные из `.env` и экспортирует:
  - `TELEGRAM_TOKEN`
  - `OPENAI_API_KEY`
  - `OPENAI_BASE_URL` (по умолчанию `https://api.proxyapi.ru/openai/v1`)
  - `OPENAI_MODEL` (по умолчанию `gpt-4.1`)
  - `ADMIN_USERNAME` — имя администратора.

## Переменные окружения

Файл `.env` должен содержать следующие значения:

```
TELEGRAM_TOKEN=<токен Telegram бота>
OPENAI_API_KEY=<ключ OpenAI>
OPENAI_BASE_URL=<опционально: адрес API OpenAI>
OPENAI_MODEL=<опционально: модель, например gpt-4.1>
```
