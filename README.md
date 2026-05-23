# UniHelp Telegram Bot

AI-чат-бот для дипломного проекта на тему:

`Чат-бот "помощник для первокурсника" для консультации 24/7`

## Назначение

Бот помогает первокурсникам получать быстрые консультации по типовым вопросам:
- адаптация в первые недели обучения
- стипендия и выплаты
- общежитие
- общение с преподавателями
- пропуски и отработки
- экзамены и сессия

## Основные функции

- Telegram-бот на `aiogram`
- генерация ответов через OpenAI GPT
- локальная база знаний по темам первокурсника
- хранение короткой истории диалога в Redis
- сохранение пользователей и сообщений в PostgreSQL
- команды `/start`, `/help`, `/about`, `/contacts`, `/faq`, `/reset`
- reply-клавиатура для быстрых сценариев

## Структура проекта

```text
app/
  ai/                интеграция AI
  bot/               Telegram handlers, runner, keyboards
  core/              конфигурация и логирование
  data/              локальные материалы и справочные данные
  database/          подключение к PostgreSQL и Redis
  repositories/      работа с историей чата и пользовательской активностью
  services/          бизнес-логика бота
```

## Используемые технологии

- Python 3.12
- aiogram 3
- OpenAI Python SDK
- FastAPI
- PostgreSQL
- Redis
- SQLAlchemy
- Alembic
- Loguru

## Переменные окружения

Заполнить `.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/bot
CONNECTION_COUNT=10
ADDITIONAL_CONNECTIONS=0
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=10
ENABLE_RATE_LIMITER=False
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_ADMIN_IDS=123456789
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4.1-mini
OPENAI_TIMEOUT_SECONDS=15
ASSISTANT_NAME=UniHelp
CHAT_HISTORY_LIMIT=10
```

## Запуск

### 1. Установить зависимости

Если окружение еще не подготовлено:

```powershell
poetry install
```

### 2. Запустить PostgreSQL и Redis

Нужны работающие сервисы PostgreSQL и Redis.

### 3. Применить миграции

```powershell
alembic upgrade head
```

Создание таблиц выполняется только через `Alembic`. Бот не создает схему автоматически при старте.

### 4. Запустить бота

```powershell
.\.venv\Scripts\python.exe -m app.bot.runner
```

## Запуск в Docker

Для локальной проверки можно запускать проект в контейнерах.

### 1. Проверить `.env`

Убедись, что в `.env` заполнены как минимум:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_ADMIN_IDS=123456789
OPENAI_API_KEY=your_openai_api_key
```

### 2. Поднять сервисы

```powershell
docker compose up --build
```

Что произойдет:
- поднимется PostgreSQL
- поднимется Redis
- бот дождется доступности сервисов
- автоматически выполнится `alembic upgrade head`
- после этого запустится Telegram-бот

### 3. Остановить проект

```powershell
docker compose down
```

Если нужно удалить и volumes:

```powershell
docker compose down -v
```

## Архитектурная идея

1. Пользователь отправляет сообщение в Telegram.
2. `aiogram` принимает сообщение и передает его в обработчик.
3. Бот ищет подходящий локальный контекст в базе знаний.
4. История диалога извлекается из Redis.
5. Запрос отправляется в OpenAI GPT.
6. Ответ возвращается пользователю.
7. Данные о пользователе и переписке сохраняются в PostgreSQL.

## Миграции базы данных

В проект добавлен `Alembic`.

Полезные команды:

```powershell
alembic upgrade head
alembic current
alembic history
```

Если PostgreSQL запущен в Docker, а локальный `DATABASE_URL` в `.env` отличается, команды миграций удобнее выполнять внутри контейнера:

```powershell
docker compose exec bot alembic current
docker compose exec bot alembic history
docker compose exec bot alembic upgrade head
```

## Что можно улучшить дальше

- административная панель для редактирования FAQ
- интеграция с расписанием и календарем
- отдельные роли: абитуриент, первокурсник, куратор
- аналитика частых вопросов
- RAG по документам конкретного университета
- Docker-конфигурация для полного разворачивания проекта

## Идея для раздела диплома

Проект можно описывать как интеллектуальную информационно-консультационную систему, которая:
- повышает доступность консультации для первокурсников
- снижает нагрузку на кураторов и деканат
- обеспечивает быстрый доступ к типовой информации 24/7
- комбинирует генеративный AI и локальную предметную базу знаний
