from app.data.faq import FAQ_ENTRIES
from app.repositories.faq_repository import FaqRepository


class KnowledgeBaseService:
    def __init__(self, faq_repository: FaqRepository | None = None) -> None:
        self.entries = FAQ_ENTRIES
        self.faq_repository = faq_repository

    async def _get_entries(self) -> list[dict[str, object]]:
        if self.faq_repository is None:
            return self.entries

        db_entries = await self.faq_repository.list_entries(active_only=True)
        if not db_entries:
            return self.entries

        return [
            {
                "id": entry.id,
                "title": entry.title,
                "keywords": self.faq_repository.deserialize_keywords(entry.keywords),
                "content": entry.content,
                "sort_order": entry.sort_order,
            }
            for entry in db_entries
        ]

    async def build_context(self, user_message: str) -> str:
        normalized_message = user_message.lower()
        matched_entries: list[str] = []
        entries = await self._get_entries()

        for entry in entries:
            keywords = entry["keywords"]
            if any(keyword in normalized_message for keyword in keywords):
                matched_entries.append(f"- {entry['title']}: {entry['content']}")

        if not matched_entries:
            return ""

        return "Используй эти справочные материалы, если они подходят к вопросу:\n" + "\n".join(matched_entries)

    def get_default_menu_topics(self) -> list[str]:
        return [str(entry["title"]) for entry in self.entries[:4]]

    async def get_entry_by_title(self, title: str) -> str | None:
        entries = await self._get_entries()
        for entry in entries:
            if entry["title"] == title:
                return str(entry["content"])
        return None

    async def get_faq_titles(self) -> list[str]:
        entries = await self._get_entries()
        return [str(entry["title"]) for entry in entries]

    async def get_entries(self) -> list[dict[str, object]]:
        return await self._get_entries()

    async def build_fallback_response(self, user_message: str, error: str | None = None) -> str:
        normalized_message = user_message.lower()
        entries = await self._get_entries()

        for entry in entries:
            keywords = entry["keywords"]
            if any(keyword in normalized_message for keyword in keywords):
                return "AI сейчас недоступен, поэтому отвечаю по базе знаний.\n\n" + str(entry["content"])

        if error and "quota" in error.lower():
            return (
                "Сейчас внешний AI недоступен из-за ограничений API. "
                "Попробуй задать вопрос точнее или воспользуйся разделом FAQ."
            )

        return (
            "Сейчас AI недоступен, и я не нашел точного ответа в локальной базе знаний. "
            "Попробуй уточнить вопрос, факультет или воспользоваться разделом FAQ."
        )
