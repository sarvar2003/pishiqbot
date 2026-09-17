from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.keyboards.common import CB_BACK, CB_CANCEL
from app.database.models import Category

CB_CATEGORY_PREFIX = "cat:"


def categories_keyboard(categories: list[Category], columns: int = 2) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=c.display_name, callback_data=f"{CB_CATEGORY_PREFIX}{c.id}")
        for c in categories
    ]
    rows = [buttons[i : i + columns] for i in range(0, len(buttons), columns)]
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_BACK)])
    rows.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data=CB_CANCEL)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def categories_management_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=c.display_name, callback_data=f"catmanage:{c.id}")]
        for c in categories
    ]
    rows.append([InlineKeyboardButton(text="➕ Yangi kategoriya", callback_data="catmanage:new")])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_BACK)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def category_edit_keyboard(category_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Nomini o'zgartirish", callback_data=f"catrename:{category_id}")],
            [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"catdelete:{category_id}")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_BACK)],
        ]
    )


def category_type_choice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Kirim", callback_data="cattype:income"),
                InlineKeyboardButton(text="➖ Chiqim", callback_data="cattype:expense"),
            ],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_BACK)],
        ]
    )
