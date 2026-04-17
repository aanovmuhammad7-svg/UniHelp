from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from loguru import logger

from app.bot.handlers import setup_handlers
from app.core.config import settings
from app.database.database import engine
from app.database.redis import redis_client
from app.repositories.chat_history import ChatHistoryRepository
from app.repositories.user_activity import UserActivityRepository
from app.services.chat_assistant import ChatAssistantService
from app.services.knowledge_base import KnowledgeBaseService


async def run_bot() -> None:
    bot = Bot(
        token=settings.telegram_bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=settings.telegram_parse_mode),
    )
    dispatcher = Dispatcher()

    history_repository = ChatHistoryRepository(redis_client=redis_client)
    knowledge_base_service = KnowledgeBaseService()
    user_activity_repository = UserActivityRepository()
    assistant_service = ChatAssistantService(
        history_repository=history_repository,
        knowledge_base_service=knowledge_base_service,
        user_activity_repository=user_activity_repository,
    )
    setup_handlers(dispatcher, assistant_service, knowledge_base_service)

    logger.info("Telegram bot polling started")
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_bot())
