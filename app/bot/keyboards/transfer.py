from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.keyboards.common import CB_CANCEL

CB_TRANSFER_CASH_TO_CARD = "transfer:cash_to_card"
CB_TRANSFER_CARD_TO_CASH = "transfer:card_to_cash"


def transfer_direction_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💵 Naqd → 💳 Karta", callback_data=CB_TRANSFER_CASH_TO_CARD)],
            [InlineKeyboardButton(text="💳 Karta → 💵 Naqd", callback_data=CB_TRANSFER_CARD_TO_CASH)],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=CB_CANCEL)],
        ]
    )
