from aiogram import Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from loguru import logger

from app.bot.keyboards import main_menu_keyboard
from app.core.config import settings
from app.repositories.user_activity import TelegramProfile
from app.services.chat_assistant import ChatAssistantService
from app.services.knowledge_base import KnowledgeBaseService
from app.services.project_info import ProjectInfoService


def setup_handlers(
    dp: Dispatcher,
    assistant_service: ChatAssistantService,
    knowledge_base_service: KnowledgeBaseService,
) -> None:
    menu_topics = knowledge_base_service.get_menu_topics()
    menu_keyboard = main_menu_keyboard(menu_topics)
    project_info_service = ProjectInfoService()

    @dp.message(CommandStart())
    async def handle_start(message: Message) -> None:
        await message.answer(
            (
                f"Привет! Я {settings.assistant_name}, AI-помощник для первокурсника.\n\n"
                "Я могу помочь с вопросами по учебе, адаптации, общению с преподавателями, "
                "расписанию, документам и студенческой жизни.\n\n"
                "Напиши свой вопрос обычным сообщением."
            ),
            reply_markup=menu_keyboard,
        )

    @dp.message(Command("help"))
    async def handle_help(message: Message) -> None:
        await message.answer(
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
        await message.answer(project_info_service.get_about_text(), reply_markup=menu_keyboard)

    @dp.message(Command("contacts"))
    async def handle_contacts(message: Message) -> None:
        await message.answer(project_info_service.get_contacts_text(), reply_markup=menu_keyboard)

    @dp.message(Command("faq"))
    async def handle_faq(message: Message) -> None:
        await message.answer(project_info_service.get_faq_text(), reply_markup=menu_keyboard)

    @dp.message(Command("reset"))
    async def handle_reset(message: Message) -> None:
        if message.from_user is None:
            return
        await assistant_service.reset_dialog(message.from_user.id)
        await message.answer("История диалога очищена. Можем начать заново.", reply_markup=menu_keyboard)

    @dp.message(F.text.in_({"Очистить диалог", "/reset"}))
    async def handle_reset_button(message: Message) -> None:
        if message.from_user is None:
            return
        await assistant_service.reset_dialog(message.from_user.id)
        await message.answer("История диалога очищена. Жду новый вопрос.", reply_markup=menu_keyboard)

    @dp.message(F.text == "Помощь")
    async def handle_help_button(message: Message) -> None:
        await handle_help(message)

    @dp.message(F.text == "О проекте")
    async def handle_about_button(message: Message) -> None:
        await message.answer(project_info_service.get_about_text(), reply_markup=menu_keyboard)

    @dp.message(F.text == "Контакты")
    async def handle_contacts_button(message: Message) -> None:
        await message.answer(project_info_service.get_contacts_text(), reply_markup=menu_keyboard)

    @dp.message(F.text == "FAQ")
    async def handle_faq_button(message: Message) -> None:
        await message.answer(project_info_service.get_faq_text(), reply_markup=menu_keyboard)

    @dp.message(F.text.in_(set(menu_topics)))
    async def handle_menu_topic(message: Message) -> None:
        if message.text is None:
            return
        entry = knowledge_base_service.get_entry_by_title(message.text)
        if entry is None:
            return
        await message.answer(f"<b>{message.text}</b>\n\n{entry}", reply_markup=menu_keyboard)

    @dp.message(F.text)
    async def handle_text(message: Message) -> None:
        if message.from_user is None or message.text is None:
            return

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
        except RuntimeError as exc:
            logger.exception("Failed to generate assistant response")
            await message.answer(str(exc), reply_markup=menu_keyboard)
            return
        except Exception:
            logger.exception("Failed to generate assistant response")
            await message.answer(
                (
                    "Сейчас не получилось обратиться к AI-модели. "
                    "Проверь OpenAI API key, интернет-соединение и попробуй еще раз."
                ),
                reply_markup=menu_keyboard,
            )
            return

        await message.answer(answer, reply_markup=menu_keyboard)

    @dp.message()
    async def handle_unsupported(message: Message) -> None:
        await message.answer(
            "Пока я умею работать только с текстовыми сообщениями и командами.",
            reply_markup=menu_keyboard,
        )
