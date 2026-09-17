from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CB_PERIOD_PREFIX = "period:"

PERIOD_TODAY = "today"
PERIOD_YESTERDAY = "yesterday"
PERIOD_WEEK = "week"
PERIOD_MONTH = "month"
PERIOD_PREV_MONTH = "prev_month"
PERIOD_CUSTOM = "custom"


def report_period_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Bugun", callback_data=f"{CB_PERIOD_PREFIX}{PERIOD_TODAY}"),
                InlineKeyboardButton(text="Kecha", callback_data=f"{CB_PERIOD_PREFIX}{PERIOD_YESTERDAY}"),
            ],
            [
                InlineKeyboardButton(text="Shu hafta", callback_data=f"{CB_PERIOD_PREFIX}{PERIOD_WEEK}"),
                InlineKeyboardButton(text="Shu oy", callback_data=f"{CB_PERIOD_PREFIX}{PERIOD_MONTH}"),
            ],
            [
                InlineKeyboardButton(
                    text="O'tgan oy", callback_data=f"{CB_PERIOD_PREFIX}{PERIOD_PREV_MONTH}"
                ),
                InlineKeyboardButton(
                    text="Custom sana", callback_data=f"{CB_PERIOD_PREFIX}{PERIOD_CUSTOM}"
                ),
            ],
        ]
    )
