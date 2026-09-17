from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CB_BACK = "nav:back"
CB_CANCEL = "nav:cancel"
CB_SKIP = "nav:skip"
CB_CONFIRM = "nav:confirm"
CB_EDIT = "nav:edit"
CB_DELETE_CONFIRM = "nav:delete_confirm"
CB_DELETE_CANCEL = "nav:delete_cancel"


def back_cancel_keyboard(include_skip: bool = False) -> InlineKeyboardMarkup:
    row = [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_BACK)]
    if include_skip:
        row.append(InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data=CB_SKIP))
    return InlineKeyboardMarkup(
        inline_keyboard=[row, [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=CB_CANCEL)]]
    )


def cancel_only_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data=CB_CANCEL)]]
    )


def confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Saqlash", callback_data=CB_CONFIRM)],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_BACK)],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=CB_CANCEL)],
        ]
    )


CB_CHANGE_DATE = "nav:change_date"


def transaction_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Saqlash", callback_data=CB_CONFIRM)],
            [InlineKeyboardButton(text="📅 Sana/vaqtni o'zgartirish", callback_data=CB_CHANGE_DATE)],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_BACK)],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=CB_CANCEL)],
        ]
    )


def yes_no_keyboard(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha", callback_data=yes_data),
                InlineKeyboardButton(text="❌ Yo'q", callback_data=no_data),
            ]
        ]
    )
