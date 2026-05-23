from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


TOPIC_BUTTONS = {
    "Адаптация": "Адаптация в первые недели",
    "Стипендия": "Стипендия и выплаты",
    "Общежитие": "Общежитие",
    "Преподаватели": "Общение с преподавателем",
}

BUTTON_FAQ = "FAQ"
BUTTON_ABOUT = "О боте"
BUTTON_CONTACTS = "Контакты"
BUTTON_CLEAR_CHAT = "Очистить чат"
BUTTON_HELP = "Помощь"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="Адаптация"), KeyboardButton(text="Стипендия")],
        [KeyboardButton(text="Общежитие"), KeyboardButton(text="Преподаватели")],
        [KeyboardButton(text=BUTTON_FAQ), KeyboardButton(text=BUTTON_ABOUT)],
        [KeyboardButton(text=BUTTON_CONTACTS), KeyboardButton(text=BUTTON_HELP)],
        [KeyboardButton(text=BUTTON_CLEAR_CHAT)],
    ]
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Задай вопрос про учебу и студенческую жизнь",
    )
