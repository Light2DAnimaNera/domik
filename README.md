# domik

## Запуск

1. Создайте и активируйте виртуальное окружение.
2. Установите зависимости: `pip install -r requirements.txt`.
3. Создайте файл `.env` и заполните его своими ключами и токенами (`TELEGRAM_TOKEN`, `OPENAI_API_KEY`, `PAYMENT_TOKEN`, `SHOP_ID`).
4. Запустите бота: `python bot.py`.

   Сообщения телебота обрабатываются десятью потоками.

   Для остановки нажмите `Ctrl+C` или отправьте процессу сигнал `SIGTERM`. Бот
   завершится корректно без сообщений об ошибках.

После запуска доступны команды из файла `bot_commands.py`. При вводе `/start`
бот спрашивает, есть ли вам 18 лет, **если пользователя ещё нет в базе**. При
положительном ответе выводится системное сообщение с правилами и устанавливается
меню команд согласно роли. Если выбрать «Нет», учётная запись блокируется.
Если пользователь уже зарегистрирован, бот отвечает
«👋 С ВОЗВРАЩЕНИЕМ {username}».
Справочную информацию можно получить командой `/help`.
Команда `/help` также доступна в меню.
Бот не показывает клавиатуру с командами. Нажмите кнопку «Menu», чтобы открыть список команд.

Баланс хранится в колонке `credits` таблицы `users`. Стоимость списания рассчитывается по числу токенов: один токен запроса стоит `0.0020` единиц, токен ответа — `0.0005`. Итоговая сумма умножается на коэффициент `token_cost_coeff` из таблицы `settings` (по умолчанию он равен `1.0`). Команда `/balance` показывает текущий баланс и сегодняшние траты. В ответе оба значения выводятся с точностью до двух знаков после запятой, округляясь в большую сторону, и сопровождаются символом 🝣. Команда `/coeff` позволяет узнать тарифный коэффициент, а `/set_coeff` — изменить его. Команды `/coeff` и `/set_coeff` доступны только администратору.
Команда `/recharge` выводит кнопки с фиксированными суммами пополнения. После выбора бот создаёт ссылку для оплаты через YooKassa и отправляет её вместе с кнопкой «перейти к оплате». Оплата проверяется автоматически, успешное пополнение подтверждается сообщением.
В консоли выводятся логи со статусом оплаты от создания счёта до его завершения.
После получения от YooKassa статуса `succeeded` или `canceled` платёж удаляется из списка ожидающих и больше не запрашивается.
Новые пользователи при регистрации получают 20 кредитов на счёт.
В таблице `users` присутствует поле `blocked`. По умолчанию оно равно `0`, и
пользователь может пользоваться ботом. Если значение становится `1`, доступ
блокируется.
При каждом списании средств бот выводит в консоль, сколько токенов ушло на
отправку запроса и получение ответа, а также сообщает новый баланс
пользователя.

Для ведения диалогов предусмотрены сессии:
- `/begin` — начать новую сессию;
- `/end` — завершить текущую и сохранить её краткое описание. После закрытия
  полная история переписки выводится в консоль.
Одновременно может быть только одна активная сессия. При попытке запустить `/begin` во время
действующей сессии бот ответит: «Что бы начать новую сессию, заверши предыдущую сессию».
Если из-за внутренней ошибки создать сессию не удалось, бот сообщит: «Не удалось начать сессию».

Сессия автоматически завершается, если пользователь не отправляет сообщения более 10 минут.
Дата завершения сохраняется в базе в формате `mm-dd-yy HH-MM`.

Обычные сообщения обрабатываются только при активной сессии. Если её нет, бот
попросит запустить `/begin`.

При завершении сессии бот создаёт конспект по правилам SessionSummarizer v5.
Для генерации используются роли, время и тексты всех сообщений из базы (`SELECT role, content, created ...`).
Полный текст диалога также выводится в консоль.

Отправленные пользователем сообщения сохраняются в таблицу `messages` вместе с
отметкой времени. Дата и время фиксируются в часовом поясе Москвы
(UTC+3) в формате `mm-dd-yy HH-MM`.

При старте новой сессии бот ищет конспект последней завершённой сессии
пользователя. Если он найден, короткий текст передаётся модели в скрытом блоке
`CONTEXT_PREVIOUS_SESSION_*` перед системным промптом DOMINA. Пользователь не
видит этот блок, но бот учитывает его при ответах.

Основная логика общения с GPT и все используемые промпты находятся в модуле
`gpt_client.py`.
