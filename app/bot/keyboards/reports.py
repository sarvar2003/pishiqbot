from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CB_PERIOD_PREFIX = "period:"
CB_REPORT_PDF = "report_pdf"

PERIOD_TODAY = "today"
PERIOD_YESTERDAY = "yesterday"
PERIOD_WEEK = "week"
PERIOD_MONTH = "month"
PERIOD_PREV_MONTH = "prev_month"
PERIOD_YEAR = "year"
PERIOD_CUSTOM = "custom"


def report_period_keyboard(show_pdf: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="Bugun", callback_data=f"{CB_PERIOD_PREFIX}{PERIOD_TODAY}"),
            InlineKeyboardButton(text="Kecha", callback_data=f"{CB_PERIOD_PREFIX}{PERIOD_YESTERDAY}"),
        ],
        [
            InlineKeyboardButton(text="Shu hafta", callback_data=f"{CB_PERIOD_PREFIX}{PERIOD_WEEK}"),
            InlineKeyboardButton(text="Shu oy", callback_data=f"{CB_PERIOD_PREFIX}{PERIOD_MONTH}"),
        ],
        [
            InlineKeyboardButton(text="O'tgan oy", callback_data=f"{CB_PERIOD_PREFIX}{PERIOD_PREV_MONTH}"),
            InlineKeyboardButton(text="Bu yil", callback_data=f"{CB_PERIOD_PREFIX}{PERIOD_YEAR}"),
        ],
        [
            InlineKeyboardButton(text="Custom sana oralig'i", callback_data=f"{CB_PERIOD_PREFIX}{PERIOD_CUSTOM}"),
        ],
    ]
    if show_pdf:
        rows.append([InlineKeyboardButton(text="📄 PDF hisobot", callback_data=CB_REPORT_PDF)])
    return InlineKeyboardMarkup(inline_keyboard=rows)
