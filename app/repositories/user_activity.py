from dataclasses import dataclass

from loguru import logger
from sqlalchemy import select

from app.database.database import async_session_factory
from app.database.models.message import ChatMessage
from app.database.models.user import TelegramUser


@dataclass(slots=True)
class TelegramProfile:
    telegram_id: int
    chat_id: int
    username: str | None
    first_name: str | None
    last_name: str | None


class UserActivityRepository:
    async def upsert_user(self, profile: TelegramProfile) -> int | None:
        try:
            async with async_session_factory() as session:
                result = await session.execute(
                    select(TelegramUser).where(TelegramUser.telegram_id == profile.telegram_id)
                )
                user = result.scalar_one_or_none()
                if user is None:
                    user = TelegramUser(
                        telegram_id=profile.telegram_id,
                        username=profile.username,
                        first_name=profile.first_name,
                        last_name=profile.last_name,
                    )
                    session.add(user)
                    await session.flush()
                else:
                    user.username = profile.username
                    user.first_name = profile.first_name
                    user.last_name = profile.last_name

                await session.commit()
                return user.id
        except Exception:
            logger.exception("Failed to upsert telegram user")
            return None

    async def save_message(self, telegram_user_id: int, chat_id: int, role: str, content: str) -> None:
        try:
            async with async_session_factory() as session:
                session.add(
                    ChatMessage(
                        telegram_user_id=telegram_user_id,
                        chat_id=chat_id,
                        role=role,
                        content=content,
                    )
                )
                await session.commit()
        except Exception:
            logger.exception("Failed to save chat message")
