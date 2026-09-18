from __future__ import annotations

import datetime
from zoneinfo import ZoneInfo


def now_local(tz: ZoneInfo) -> datetime.datetime:
    return datetime.datetime.now(tz)


def start_of_day(dt: datetime.datetime) -> datetime.datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt: datetime.datetime) -> datetime.datetime:
    return start_of_day(dt) + datetime.timedelta(days=1)


def start_of_week(dt: datetime.datetime) -> datetime.datetime:
    monday = start_of_day(dt) - datetime.timedelta(days=dt.weekday())
    return monday


def start_of_month(dt: datetime.datetime) -> datetime.datetime:
    return start_of_day(dt).replace(day=1)


def start_of_next_month(dt: datetime.datetime) -> datetime.datetime:
    first = start_of_month(dt)
    if first.month == 12:
        return first.replace(year=first.year + 1, month=1)
    return first.replace(month=first.month + 1)


def start_of_previous_month(dt: datetime.datetime) -> datetime.datetime:
    first = start_of_month(dt)
    if first.month == 1:
        return first.replace(year=first.year - 1, month=12)
    return first.replace(month=first.month - 1)


def start_of_year(dt: datetime.datetime) -> datetime.datetime:
    return start_of_day(dt).replace(month=1, day=1)


def start_of_next_year(dt: datetime.datetime) -> datetime.datetime:
    return start_of_year(dt).replace(year=dt.year + 1)


def parse_date_ddmmyyyy(text: str) -> datetime.date | None:
    try:
        return datetime.datetime.strptime(text.strip(), "%d.%m.%Y").date()
    except ValueError:
        return None


def parse_time_hhmm(text: str) -> datetime.time | None:
    try:
        return datetime.datetime.strptime(text.strip(), "%H:%M").time()
    except ValueError:
        return None
