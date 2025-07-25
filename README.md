# domik

## Версии

Каждый бот имеет собственный номер версии, сохранённый в файле `bots/<имя>/__init__.py` в виде переменной `__version__`.
Формат `X.Y.Z` означает:

- `X` — мажорные изменения с добавлением глобального функционала или совершенно нового;
- `Y` — доработка имеющегося функционала;
- `Z` — багфиксы и хотфиксы.

Текущая версия всех ботов: `1.1.10`.

## Запуск

### Быстрый старт

1. Установите Python 3.11 или новее с сайта python.org.
2. Скачайте проект и распакуйте его в удобную папку.
3. Откройте эту папку в командной строке и выполните `python -m venv venv`. Затем активируйте окружение.
4. Установите зависимости: `pip install -r requirements.txt`.
5. Создайте файл `.env` и впишите в него свои токены и ID чатов.
6. Запустите бота командой `python run.py DSS` (или другой вариант из списка).

1. Создайте и активируйте виртуальное окружение.
2. Установите зависимости: `pip install -r requirements.txt`.
   Файл включает библиотеки `pytelegrambotapi`, `openai`, `python-dotenv`,
   `yookassa`, `requests` и `tzdata`.
3. Создайте файл `.env` и заполните его своими ключами и токенами (`TELEGRAM_TOKEN_BOT1`, `TELEGRAM_TOKEN_BOT2`, `TELEGRAM_TOKEN_BOT3`, `OPENAI_API_KEY`, `PAYMENT_TOKEN`, `SHOP_ID`, `DSA_REPORT_CHAT_ID`, `ADMIN_USERNAME`, `DSS_FORUM_ID`). При необходимости можно указать `DB_PATH` и `DSS_DB_PATH` с абсолютными путями к файлам баз данных. Значение `DSA_REPORT_CHAT_ID` может содержать несколько ID чатов, разделённых запятыми.
4. Запустите нужного бота командой `python run.py DS` (или `DSA`, `DSS`). Или используйте `run_DS.bat`, `run_DSA.bat` или `run_DSS.bat`.
5. В консоли появится сообщение вида «Запуск бота DS», где `DS` — выбранный бот.

   Сообщения телебота обрабатываются тридцатью потоками.

   Каждый вызов `get_connection()` из модуля `shared.database` возвращает
   новое соединение, поэтому потоки не делят общий объект базы данных.

   Для остановки нажмите `Ctrl+C` или отправьте процессу сигнал `SIGTERM`. Бот
   завершится корректно без сообщений об ошибках.

После запуска доступны команды из файла `bots/<bot>/bot_commands.py`. При вводе `/start`
бот спрашивает, есть ли вам 18 лет, **если пользователя ещё нет в базе**. При
положительном ответе выводится системное сообщение с правилами и устанавливается
меню команд. Если выбрать «Нет», учётная запись блокируется.
Если пользователь уже зарегистрирован, бот отвечает
«👋 С ВОЗВРАЩЕНИЕМ {username}».
Справочную информацию можно получить командой `/help`.
Команда `/help` также доступна в меню и содержит контакт поддержки @DominaSupremaSupportBot.
Бот не показывает клавиатуру с командами. Нажмите кнопку «Menu», чтобы открыть список команд.

Баланс хранится в колонке `credits` таблицы `users`. Стоимость списания рассчитывается по числу токенов: один токен запроса стоит `0.0004` единиц, токен ответа — `0.0001`. Итоговая сумма умножается на коэффициент `token_cost_coeff` из таблицы `settings` (по умолчанию он равен `12.0`). Команда `/balance` показывает текущий баланс и сегодняшние траты. В ответе оба значения выводятся с точностью до двух знаков после запятой, округляясь в большую сторону, и сопровождаются символом 🝣.
Команда `/recharge` выводит кнопки с фиксированными суммами пополнения. После выбора бот просит указать email для получения чека и только затем создаёт ссылку для оплаты через YooKassa, отправляя её вместе с кнопкой «перейти к оплате». Оплата проверяется автоматически, успешное пополнение подтверждается сообщением. Введённый email проверяется. При ошибке бот отвечает: «Email введен не верно, укажите корректный email. Он будет использован только для отправки фискального документа.»
В консоль выводятся логи со статусом оплаты и данными, отправляемыми в YooKassa, от создания счёта до его завершения. Дополнительно сведения сохраняются в таблицу `payments`: в ней для каждого платёжного идентификатора хранится единственная запись, где обновляется текущий статус, время `mm-dd-yy HH-MM` и количество начисленных кредитов. При ошибке обращения к YooKassa бот выводит текст исключения в лог, что помогает найти причину проблемы с токеном или магазином.
После получения от YooKassa статуса `succeeded` или `canceled` платёж удаляется из списка ожидающих и больше не запрашивается.
При успешной оплате бот DS отправляет в бот DSA уведомление вида:
«НОВОЕ ПОСТУПЛЕНИЕ\nПользователь @username через сервис YooKassa\nОплатил подписку на {amount} ₽».
Новые пользователи при регистрации получают 100 кредитов на счёт.
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

При завершении сессии бот создаёт конспект по правилам SessionSummarizer v10.
Для генерации используются роли, время и тексты всех сообщений из базы (`SELECT role, content, created ...`).
Максимальная длина конспекта составляет 5000 символов.
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
Функция `make_summary(previous_summary, session_history)` этого модуля
возвращает не более `SUMMARY_CHAR_LIMIT` символов (5000) обновлённого
конспекта на основе предыдущего резюме и новой истории диалога.

### DSA

Бот `DSA` рассылает ежедневный отчет об активности. В 23:59 по московскому времени
он отправляет сообщение в чаты, ID которых перечислены в переменной
`DSA_REPORT_CHAT_ID`. Тот же отчет можно получить командой `/report`.
Для запуска рассылки по базе предусмотрена команда `/newsletter`,
которая показывает инлайн-клавиатуру с цифрами 1–5 и список вариантов аудитории.
После нажатия выбранная клавиатура скрывается, чтобы исключить повторный выбор.
Бот сразу сообщает администратору выбранный пункт текстом
«выбран вариант X», где X соответствует описанию варианта.
Если команда вызывается повторно до завершения текущей рассылки,
незавершённый черновик автоматически получает статус «canceled».
После выбора аудитории администратор отправляет пост. Он может содержать одно изображение. Бот сохраняет его как
черновик и копирует обратно с двумя кнопками «Далее» и «Изменить». Если в посте есть фото,
бот скачивает изображение через текущий экземпляр бота и пересылает его через DS, чтобы получить `file_id` этого бота, после чего удаляет копию. Кнопка
«Далее» подтверждает черновик, «Изменить» удаляет сохранённый пост и запрашивает
новый.
После подтверждения бот спрашивает, когда отправить сообщение. Кнопки
«Отправить сейчас» и «Отложенный запуск» отправляются инлайн. Во втором случае необходимо указать
дату и время в формате `DD.MM.YYYY HH:MM` по московскому времени. Если введено
некорректное значение, бот сообщает об ошибке и просит повторить ввод. Если
указанная дата и время по Москве меньше или равна текущему моменту, бот выводит сообщение «введенное время уже истекло»
и также предлагает указать данные заново. При правильном формате он подтверждает расписание и
отвечает: «Сообщения будут разосланы согласно выбранным критериям».
При выборе варианта «Отправить сейчас» рассылка помещается в очередь со статусом
`scheduled` и отправляется фоновым планировщиком в течение минуты. После
успешной отправки планировщик сразу меняет статус записи на `sent` и фиксирует
время в поле `sent_at`.
После завершения отправки в администраторский чат приходит сообщение вида
`рассылка с id=<id> отправлена, оповещено N пользователей`, где `N` — число
получателей. Если бот DSA недоступен, но переменная `DSA_REPORT_CHAT_ID` задана,
то то же уведомление отправляет бот DS.
Черновики и готовые к отправке посты сохраняются в таблице `newsletters`
файла `users.db`. Таблица фиксирует текст и изображение рассылки, аудиторию и статус.
Получатели выбираются SQL-функциями `all_newsletter`, `buyers_newsletter`,
`low_balance_newsletter`, `idle_newsletter` и `no_sessions_newsletter`.
Записи со статусом `scheduled` раз в минуту проверяет фоновый планировщик,
который запускается в боте DS. Если время отправки меньше текущего,
сообщение рассылается выбранной аудитории, поле `sent_at` заполняется
текущим моментом и статус меняется на `sent`.
Первая строка отчета содержит дату и время вида `20 июня, 23:59`.
Сумма платежей в отчете показывается в рублях, рядом с цифрами печатается знак ₽. Строка «На сумму» отражает сколько средств пользователи внесли за день.
Знак ₽ также выводится в строке «Из них первый платеж:».
В этом поле суммируются только первые пополнения каждого пользователя,
повторные операции не учитываются.
Количество новых пользователей рассчитывается по дате регистрации в московском
часовом поясе и не зависит от числа запросов отчёта за день.
Доступ к боту ограничен: обращаться к нему могут только пользователи,
чьи имена указаны в `ADMIN_USERNAME`.
Бот выводит подробные сообщения в лог: фиксируется выбор аудитории,
сохранение черновиков, планирование и отправка рассылок,
а также отправка ежедневных отчётов.
Дополнительные команды:
- `/nl_list` — список неотправленных рассылок вида `[ID] [дата/время] [audience] [status] «первые 30 символов...»`
 - `/nl_cancel <id>` — отменить рассылку по ID (меняет статус на `canceled`). Если ID существует, бот отвечает «рассылка `<id>` отменена». Если ID не существует или уже использован, бот отвечает «ID рассылки указано не верно»
- `/nl_show <id>` — присылает содержимое поста по ID

Если ID не указан, бот предложит ввести его отдельным сообщением.


### DSS

Бот `DSS` соединяет клиентов с операторами в форуме. При каждом новом личном
сообщении бот ищет связку `user_id` ↔ `topic_id` в базе `dss_topics.db` (таблица
`tickets`). Если записи нет, создаётся топик в супергруппе `DSS_FORUM_ID` с
названием «Имя Фамилия • ID» и эта пара сохраняется. В топик сначала
отправляется паспорт клиента: имя, `@username` и ID. Затем публикуется текст
сообщения в формате `[Имя] пишет:\n<текст>`. Все последующие обращения
добавляются тем же способом. Ответы операторов из топика бот пересылает
пользователю без подписи, сохраняя иллюзию личного диалога. При этом
сообщение приходит от бота DS, а не от DSS.
