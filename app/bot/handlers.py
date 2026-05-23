from aiogram import Dispatcher, F
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message
from loguru import logger
import asyncio

from app.bot.keyboards import (
    BUTTON_ABOUT,
    BUTTON_CLEAR_CHAT,
    BUTTON_CONTACTS,
    BUTTON_FAQ,
    BUTTON_HELP,
    TOPIC_BUTTONS,
    main_menu_keyboard,
)
from app.core.config import settings
from app.repositories.chat_cleanup import ChatCleanupRepository
from app.repositories.faq_repository import FaqPayload
from app.repositories.user_activity import TelegramProfile
from app.services.chat_assistant import ChatAssistantService
from app.services.knowledge_base import KnowledgeBaseService
from app.services.project_info import ProjectInfoService


def setup_handlers(
    dp: Dispatcher,
    assistant_service: ChatAssistantService,
    knowledge_base_service: KnowledgeBaseService,
    cleanup_repository: ChatCleanupRepository,
) -> None:
    menu_keyboard = main_menu_keyboard()
    project_info_service = ProjectInfoService()

    def is_admin(message: Message) -> bool:
        return message.from_user is not None and message.from_user.id in settings.telegram_admin_ids

    def parse_admin_payload(raw_args: str, with_id: bool = False) -> tuple[int | None, FaqPayload] | None:
        parts = [part.strip() for part in raw_args.split("|")]
        expected_parts = 4 if with_id else 3
        if len(parts) != expected_parts:
            return None

        entry_id: int | None = None
        if with_id:
            try:
                entry_id = int(parts[0])
            except ValueError:
                return None
            parts = parts[1:]

        title, keywords_raw, content = parts
        keywords = [keyword.strip().lower() for keyword in keywords_raw.split(",") if keyword.strip()]
        if not title or not keywords or not content:
            return None

        return entry_id, FaqPayload(title=title, keywords=keywords, content=content)

    async def faq_titles_text() -> str:
        faq_titles = await knowledge_base_service.get_faq_titles()
        return "Частые темы, по которым бот уже умеет подсказывать:\n" + "\n".join(
            f"- {title}" for title in faq_titles
        )

    def welcome_text() -> str:
        return (
            f"Привет! Я {settings.assistant_name}, AI-помощник для первокурсника.\n\n"
            "Я помогаю с вопросами по учебе, адаптации, расписанию, документам, "
            "общежитию, стипендии и студенческой жизни.\n\n"
            "Что я умею:\n"
            "- отвечать на вопросы в формате 24/7\n"
            "- подсказывать по типовым ситуациям первокурсника\n"
            "- показывать FAQ и полезные контакты\n\n"
            "Доступные команды:\n"
            "/help - список команд\n"
            "/about - информация о боте\n"
            "/contacts - полезные контакты\n"
            "/faq - список тем\n"
            "/reset - сбросить контекст диалога\n\n"
            "Можешь выбрать кнопку в меню или просто написать свой вопрос."
        )

    async def track_message(message: Message) -> None:
        await cleanup_repository.add_message_id(message.chat.id, message.message_id)

    async def send_and_track(message: Message, text: str, **kwargs: object) -> Message:
        sent_message = await message.answer(text, **kwargs)
        await cleanup_repository.add_message_id(message.chat.id, sent_message.message_id)
        return sent_message

    async def clear_tracked_chat(message: Message) -> None:
        tracked_ids = await cleanup_repository.get_message_ids(message.chat.id)
        tracked_ids = list(dict.fromkeys([message.message_id, *tracked_ids]))

        for message_id in tracked_ids:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=message_id)
            except Exception:
                logger.debug("Could not delete message {}", message_id)

        await cleanup_repository.clear_message_ids(message.chat.id)
        await assistant_service.reset_dialog(message.from_user.id if message.from_user else message.chat.id)

    async def delete_later(message: Message, delay_seconds: int = 5) -> None:
        await asyncio.sleep(delay_seconds)
        try:
            await message.delete()
        except Exception:
            logger.debug("Could not delete delayed message {}", message.message_id)

    @dp.message(CommandStart())
    async def handle_start(message: Message) -> None:
        await track_message(message)
        await send_and_track(
            message,
            welcome_text(),
            reply_markup=menu_keyboard,
        )

    @dp.message(Command("help"))
    async def handle_help(message: Message) -> None:
        await track_message(message)
        await send_and_track(
            message,
            (
                "Доступные команды:\n"
                "/start - приветствие\n"
                "/help - список команд\n"
                "/about - информация о проекте\n"
                "/contacts - полезные контакты\n"
                "/faq - список тем\n"
                "/reset - очистить историю диалога\n\n"
                "Можно писать свой вопрос текстом или использовать кнопки меню."
            ),
            reply_markup=menu_keyboard,
        )

    @dp.message(Command("about"))
    async def handle_about(message: Message) -> None:
        await track_message(message)
        await send_and_track(message, project_info_service.get_about_text(), reply_markup=menu_keyboard)

    @dp.message(Command("contacts"))
    async def handle_contacts(message: Message) -> None:
        await track_message(message)
        await send_and_track(message, project_info_service.get_contacts_text(), reply_markup=menu_keyboard)

    @dp.message(Command("faq"))
    async def handle_faq(message: Message) -> None:
        await track_message(message)
        await send_and_track(message, await faq_titles_text(), reply_markup=menu_keyboard)

    @dp.message(Command("admin_help"))
    async def handle_admin_help(message: Message) -> None:
        if not is_admin(message):
            return
        await track_message(message)
        await send_and_track(
            message,
            (
                "Админ-команды:\n"
                "/admin_faq - список FAQ\n"
                "/admin_add_faq Заголовок | ключ1,ключ2 | текст\n"
                "/admin_update_faq id | Заголовок | ключ1,ключ2 | текст\n"
                "/admin_delete_faq id"
            ),
            reply_markup=menu_keyboard,
        )

    @dp.message(Command("admin_faq"))
    async def handle_admin_faq(message: Message) -> None:
        if not is_admin(message):
            return
        await track_message(message)
        entries = await knowledge_base_service.get_entries()
        lines = ["FAQ entries:"]
        for entry in entries:
            entry_id = entry.get("id", "-")
            lines.append(f"{entry_id}: {entry['title']}")
        await send_and_track(message, "\n".join(lines), reply_markup=menu_keyboard)

    @dp.message(Command("admin_add_faq"))
    async def handle_admin_add_faq(message: Message, command: CommandObject) -> None:
        if not is_admin(message):
            return
        await track_message(message)
        parsed = parse_admin_payload(command.args or "", with_id=False)
        if parsed is None:
            await send_and_track(
                message,
                "Формат: /admin_add_faq Заголовок | ключ1,ключ2 | текст",
                reply_markup=menu_keyboard,
            )
            return
        _, payload = parsed
        repository = knowledge_base_service.faq_repository
        if repository is None:
            await send_and_track(message, "FAQ repository is not configured.", reply_markup=menu_keyboard)
            return
        entry = await repository.create_entry(payload)
        if entry is None:
            await send_and_track(message, "Не удалось создать FAQ-запись.", reply_markup=menu_keyboard)
            return
        await send_and_track(message, f"FAQ добавлен: {entry.id} - {entry.title}", reply_markup=menu_keyboard)

    @dp.message(Command("admin_update_faq"))
    async def handle_admin_update_faq(message: Message, command: CommandObject) -> None:
        if not is_admin(message):
            return
        await track_message(message)
        parsed = parse_admin_payload(command.args or "", with_id=True)
        if parsed is None:
            await send_and_track(
                message,
                "Формат: /admin_update_faq id | Заголовок | ключ1,ключ2 | текст",
                reply_markup=menu_keyboard,
            )
            return
        entry_id, payload = parsed
        repository = knowledge_base_service.faq_repository
        if repository is None or entry_id is None:
            await send_and_track(message, "FAQ repository is not configured.", reply_markup=menu_keyboard)
            return
        entry = await repository.update_entry(entry_id, payload)
        if entry is None:
            await send_and_track(message, "FAQ-запись не найдена или не обновлена.", reply_markup=menu_keyboard)
            return
        await send_and_track(message, f"FAQ обновлен: {entry.id} - {entry.title}", reply_markup=menu_keyboard)

    @dp.message(Command("admin_delete_faq"))
    async def handle_admin_delete_faq(message: Message, command: CommandObject) -> None:
        if not is_admin(message):
            return
        await track_message(message)
        try:
            entry_id = int((command.args or "").strip())
        except ValueError:
            await send_and_track(message, "Формат: /admin_delete_faq id", reply_markup=menu_keyboard)
            return
        repository = knowledge_base_service.faq_repository
        if repository is None:
            await send_and_track(message, "FAQ repository is not configured.", reply_markup=menu_keyboard)
            return
        deleted = await repository.delete_entry(entry_id)
        if not deleted:
            await send_and_track(message, "FAQ-запись не найдена.", reply_markup=menu_keyboard)
            return
        await send_and_track(message, f"FAQ-запись {entry_id} удалена.", reply_markup=menu_keyboard)

    @dp.message(Command("reset"))
    async def handle_reset(message: Message) -> None:
        if message.from_user is None:
            return
        await track_message(message)
        await assistant_service.reset_dialog(message.from_user.id)
        await send_and_track(message, "История диалога очищена. Можем начать заново.", reply_markup=menu_keyboard)

    @dp.message(F.text == "/reset")
    async def handle_reset_button(message: Message) -> None:
        if message.from_user is None:
            return
        await track_message(message)
        await assistant_service.reset_dialog(message.from_user.id)
        await send_and_track(message, "История диалога очищена. Жду новый вопрос.", reply_markup=menu_keyboard)

    @dp.message(F.text == BUTTON_CLEAR_CHAT)
    async def handle_clear_chat_button(message: Message) -> None:
        await track_message(message)
        await clear_tracked_chat(message)
        status_message = await message.answer("Чат очищен. Сейчас начнем заново...")
        asyncio.create_task(delete_later(status_message, delay_seconds=5))
        welcome_message = await message.answer(welcome_text(), reply_markup=menu_keyboard)
        await cleanup_repository.add_message_id(message.chat.id, welcome_message.message_id)

    @dp.message(F.text == BUTTON_HELP)
    async def handle_help_button(message: Message) -> None:
        await handle_help(message)

    @dp.message(F.text == BUTTON_ABOUT)
    async def handle_about_button(message: Message) -> None:
        await track_message(message)
        await send_and_track(message, project_info_service.get_about_text(), reply_markup=menu_keyboard)

    @dp.message(F.text == BUTTON_CONTACTS)
    async def handle_contacts_button(message: Message) -> None:
        await track_message(message)
        await send_and_track(message, project_info_service.get_contacts_text(), reply_markup=menu_keyboard)

    @dp.message(F.text == BUTTON_FAQ)
    async def handle_faq_button(message: Message) -> None:
        await track_message(message)
        await send_and_track(message, await faq_titles_text(), reply_markup=menu_keyboard)

    @dp.message(F.text.in_(set(TOPIC_BUTTONS.keys())))
    async def handle_menu_topic(message: Message) -> None:
        if message.text is None:
            return
        await track_message(message)
        faq_title = TOPIC_BUTTONS.get(message.text, message.text)
        entry = await knowledge_base_service.get_entry_by_title(faq_title)
        if entry is None:
            return
        await send_and_track(message, f"<b>{faq_title}</b>\n\n{entry}", reply_markup=menu_keyboard)

    @dp.message(F.text)
    async def handle_text(message: Message) -> None:
        if message.from_user is None or message.text is None:
            return

        await track_message(message)
        await message.bot.send_chat_action(message.chat.id, "typing")
        profile = TelegramProfile(
            telegram_id=message.from_user.id,
            chat_id=message.chat.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
        try:
            answer = await assistant_service.answer(
                user_id=message.from_user.id,
                user_message=message.text,
                chat_id=message.chat.id,
                profile=profile,
            )
        except Exception:
            logger.exception("Failed to generate assistant response")
            await send_and_track(
                message,
                (
                    "Сейчас не получилось обратиться к AI-модели. "
                    "Проверь OpenAI API key, интернет-соединение и попробуй еще раз."
                ),
                reply_markup=menu_keyboard,
            )
            return

        await send_and_track(message, answer, reply_markup=menu_keyboard)

    @dp.message()
    async def handle_unsupported(message: Message) -> None:
        await track_message(message)
        await send_and_track(
            message,
            "Пока я умею работать только с текстовыми сообщениями и командами.",
            reply_markup=menu_keyboard,
        )
