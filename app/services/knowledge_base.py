from app.data.faq import FAQ_ENTRIES


class KnowledgeBaseService:
    def __init__(self) -> None:
        self.entries = FAQ_ENTRIES

    def build_context(self, user_message: str) -> str:
        normalized_message = user_message.lower()
        matched_entries: list[str] = []

        for entry in self.entries:
            keywords = entry["keywords"]
            if any(keyword in normalized_message for keyword in keywords):
                matched_entries.append(f"- {entry['title']}: {entry['content']}")

        if not matched_entries:
            return ""

        return "Используй эти справочные материалы, если они подходят к вопросу:\n" + "\n".join(matched_entries)

    def get_menu_topics(self) -> list[str]:
        return [str(entry["title"]) for entry in self.entries[:4]]

    def get_entry_by_title(self, title: str) -> str | None:
        for entry in self.entries:
            if entry["title"] == title:
                return str(entry["content"])
        return None
