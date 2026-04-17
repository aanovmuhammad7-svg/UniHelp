from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard(menu_topics: list[str]) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=menu_topics[0]), KeyboardButton(text=menu_topics[1])],
        [KeyboardButton(text=menu_topics[2]), KeyboardButton(text=menu_topics[3])],
        [KeyboardButton(text="FAQ"), KeyboardButton(text="О проекте")],
        [KeyboardButton(text="Контакты"), KeyboardButton(text="Очистить диалог")],
        [KeyboardButton(text="Помощь")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Задай вопрос про учебу и студенческую жизнь",
    )
