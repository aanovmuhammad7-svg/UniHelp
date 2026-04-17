from app.data.faq import FAQ_ENTRIES
from app.data.info import PROJECT_ABOUT_TEXT, PROJECT_CONTACTS_TEXT, PROJECT_FEATURES_TEXT


class ProjectInfoService:
    def get_about_text(self) -> str:
        return PROJECT_ABOUT_TEXT

    def get_contacts_text(self) -> str:
        return PROJECT_CONTACTS_TEXT

    def get_features_text(self) -> str:
        return PROJECT_FEATURES_TEXT

    def get_faq_text(self) -> str:
        lines = ["Частые темы, по которым бот уже умеет подсказывать:"]
        for entry in FAQ_ENTRIES:
            lines.append(f"- {entry['title']}")
        return "\n".join(lines)
