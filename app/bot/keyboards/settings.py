from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CB_SETTINGS_CATEGORIES = "settings:categories"


def settings_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗂 Kategoriyalar", callback_data=CB_SETTINGS_CATEGORIES)],
        ]
    )
