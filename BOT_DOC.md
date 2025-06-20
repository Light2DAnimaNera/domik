# Документация по боту

## Команды бота

- `/start` — выводит приветствие.
- `/all_users` — выводит список всех пользователей. Доступно только администратору.
- `/begin` — начинает диалоговую сессию и сохраняет сообщения.
- `/end` — завершает текущую сессию, создаёт краткий конспект переписки.

## Файлы и функции

### `bot.py`
- Создаёт объект `TeleBot`, регистрирует команды и запускает бесконечный polling.

### `bot_commands.py`
- `DEFAULT_COMMANDS` — список команд бота.
- `setup_default_commands(bot)` — регистрирует их в Telegram.

### `database.py`
- `init_db()` — инициализирует базу данных SQLite и создаёт таблицы `users`, `sessions` и `messages` при первом запуске.
- `get_connection()` — возвращает соединение с базой данных.

### `config.py`
- Хранит настройки:
  - `MODEL_NAME` — название модели OpenAI;
  - `SYSTEM_PROMPT` — системный промпт для общения с GPT;
  - `CONTEXT_LIMIT` — максимальная длина контекста;
  - `DB_PATH` — путь к файлу базы данных.

### `gpt_client.py`
- Класс `GptClient` — обёртка над API OpenAI.
  - `__init__()` — создаёт клиента OpenAI с параметрами из переменных окружения.
  - `ask_gpt(user_text)` — отправляет текст пользователя в модель и возвращает ответ.

### `models.py`
- `add_user_if_not_exists(message)` — добавляет пользователя в базу, если его там ещё нет.
- `get_all_users()` — возвращает список всех пользователей.

### `session_manager.py`
- Класс `SessionManager` управляет диалоговыми сессиями:
  - `start(user)` — создаёт новую сессию;
  - `ensure(user)` — возвращает активную сессию или создаёт новую;
  - `close(user_id, summary)` — завершает сессию;
  - `active(user_id)` — получает текущую сессию пользователя.

### `message_logger.py`
- Класс `MessageLogger` сохраняет сообщения и формирует контекст диалога:
  - `log(session_id, role, content)` — пишет сообщение в базу и кэш;
  - `context(session_id)` — возвращает историю сообщений в пределах ограничения.

### `summarizer.py`
- Функция `make_summary(session_id)` — запрашивает у GPT краткий конспект сообщений сессии.

### `handlers.py`
- Функция `register_handlers(bot)` регистрирует обработчики:
  - `cmd_start(message)` — обрабатывает команду `/start` и отправляет приветствие.
  - `cmd_all_users(message)` — обрабатывает команду `/all_users` (только для админа).
  - `cmd_begin(message)` — запускает новую сессию.
  - `cmd_end(message)` — завершает сессию и сохраняет её краткое резюме.
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
