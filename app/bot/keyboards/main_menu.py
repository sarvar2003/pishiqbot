from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_INCOME = "➕ Kirim"
BTN_EXPENSE = "➖ Chiqim"
BTN_REPORT = "📊 Hisobot"
BTN_BALANCE = "💰 Balans"
BTN_TRANSACTIONS = "📋 Tranzaksiyalar"
BTN_TRANSFER = "🔄 Pul o'tkazish"
BTN_SETTINGS = "⚙️ Sozlamalar"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_INCOME), KeyboardButton(text=BTN_EXPENSE)],
            [KeyboardButton(text=BTN_REPORT), KeyboardButton(text=BTN_BALANCE)],
            [KeyboardButton(text=BTN_TRANSACTIONS)],
            [KeyboardButton(text=BTN_TRANSFER), KeyboardButton(text=BTN_SETTINGS)],
        ],
        resize_keyboard=True,
    )
