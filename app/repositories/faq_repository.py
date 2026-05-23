from dataclasses import dataclass

from loguru import logger
from sqlalchemy import select

from app.database.database import async_session_factory
from app.database.models.faq import FaqEntry


@dataclass(slots=True)
class FaqPayload:
    title: str
    keywords: list[str]
    content: str
    sort_order: int = 0
    is_active: bool = True


class FaqRepository:
    @staticmethod
    def serialize_keywords(keywords: list[str]) -> str:
        return ",".join(keyword.strip() for keyword in keywords if keyword.strip())

    @staticmethod
    def deserialize_keywords(keywords: str) -> list[str]:
        return [keyword.strip() for keyword in keywords.split(",") if keyword.strip()]

    async def list_entries(self, active_only: bool = True) -> list[FaqEntry]:
        try:
            async with async_session_factory() as session:
                query = select(FaqEntry).order_by(FaqEntry.sort_order.asc(), FaqEntry.id.asc())
                if active_only:
                    query = query.where(FaqEntry.is_active.is_(True))
                result = await session.execute(query)
                return list(result.scalars().all())
        except Exception:
            logger.exception("Failed to fetch FAQ entries")
            return []

    async def get_entry_by_title(self, title: str) -> FaqEntry | None:
        try:
            async with async_session_factory() as session:
                result = await session.execute(
                    select(FaqEntry).where(FaqEntry.title == title, FaqEntry.is_active.is_(True))
                )
                return result.scalar_one_or_none()
        except Exception:
            logger.exception("Failed to fetch FAQ entry by title")
            return None

    async def create_entry(self, payload: FaqPayload) -> FaqEntry | None:
        try:
            async with async_session_factory() as session:
                entry = FaqEntry(
                    title=payload.title,
                    keywords=self.serialize_keywords(payload.keywords),
                    content=payload.content,
                    sort_order=payload.sort_order,
                    is_active=payload.is_active,
                )
                session.add(entry)
                await session.commit()
                await session.refresh(entry)
                return entry
        except Exception:
            logger.exception("Failed to create FAQ entry")
            return None

    async def update_entry(self, entry_id: int, payload: FaqPayload) -> FaqEntry | None:
        try:
            async with async_session_factory() as session:
                result = await session.execute(select(FaqEntry).where(FaqEntry.id == entry_id))
                entry = result.scalar_one_or_none()
                if entry is None:
                    return None
                entry.title = payload.title
                entry.keywords = self.serialize_keywords(payload.keywords)
                entry.content = payload.content
                entry.sort_order = payload.sort_order
                entry.is_active = payload.is_active
                await session.commit()
                await session.refresh(entry)
                return entry
        except Exception:
            logger.exception("Failed to update FAQ entry")
            return None

    async def delete_entry(self, entry_id: int) -> bool:
        try:
            async with async_session_factory() as session:
                result = await session.execute(select(FaqEntry).where(FaqEntry.id == entry_id))
                entry = result.scalar_one_or_none()
                if entry is None:
                    return False
                await session.delete(entry)
                await session.commit()
                return True
        except Exception:
            logger.exception("Failed to delete FAQ entry")
            return False
