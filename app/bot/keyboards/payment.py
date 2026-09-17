from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.keyboards.common import CB_BACK, CB_CANCEL
from app.database.models import PaymentMethod

CB_PAYMENT_PREFIX = "pay:"

PAYMENT_LABELS = {
    PaymentMethod.cash: "💵 Naqd",
    PaymentMethod.card: "💳 Karta",
}


def payment_method_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=PAYMENT_LABELS[PaymentMethod.cash],
                    callback_data=f"{CB_PAYMENT_PREFIX}{PaymentMethod.cash.value}",
                ),
                InlineKeyboardButton(
                    text=PAYMENT_LABELS[PaymentMethod.card],
                    callback_data=f"{CB_PAYMENT_PREFIX}{PaymentMethod.card.value}",
                ),
            ],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_BACK)],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=CB_CANCEL)],
        ]
    )
