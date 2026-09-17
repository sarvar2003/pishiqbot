from __future__ import annotations

import datetime


def format_amount(amount: int) -> str:
    """Format an integer so'm amount with thin-space thousands separators, Uzbek style."""
    sign = "-" if amount < 0 else ""
    grouped = f"{abs(amount):,}".replace(",", " ")
    return f"{sign}{grouped} so'm"


def format_signed_amount(amount: int) -> str:
    sign = "+" if amount > 0 else ("-" if amount < 0 else "")
    return f"{sign}{format_amount(abs(amount))}"


def format_date(dt: datetime.datetime) -> str:
    return dt.strftime("%d.%m.%Y")


def format_date_short(dt: datetime.datetime) -> str:
    return dt.strftime("%d.%m")


def format_datetime(dt: datetime.datetime) -> str:
    return dt.strftime("%d.%m.%Y %H:%M")


def format_percent(part: int, total: int) -> str:
    if total <= 0:
        return "0%"
    return f"{(part / total * 100):.0f}%"
