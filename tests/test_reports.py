from __future__ import annotations

import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import CategoryType, PaymentMethod, TransactionType, User
from app.database.repositories.category_repo import CategoryRepository
from app.database.repositories.transaction_repo import TransactionRepository
from app.services.report_service import ReportService
from app.services.transaction_service import TransactionService

TASHKENT = ZoneInfo("Asia/Tashkent")


async def _add(service, user, type_, amount, category, method, when):
    await service.add_income_or_expense(
        user_id=user.id, type_=type_, amount=amount, category=category, payment_method=method, transaction_date=when
    )


async def test_monthly_report_calculation(session: AsyncSession, user: User) -> None:
    service = TransactionService(session, TransactionRepository(session), CategoryRepository(session))
    income_cat = (await CategoryRepository(session).list_for_user(user.id, CategoryType.income))[0]
    expense_cat = (await CategoryRepository(session).list_for_user(user.id, CategoryType.expense))[0]

    now = datetime.datetime.now(TASHKENT)
    this_month = now.replace(day=15, hour=10, minute=0, second=0, microsecond=0)
    last_month = (now.replace(day=1) - datetime.timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)

    await _add(service, user, TransactionType.income, 8_500_000, income_cat, PaymentMethod.card, this_month)
    await _add(service, user, TransactionType.expense, 3_200_000, expense_cat, PaymentMethod.card, this_month)
    # Outside the current month - must not be counted.
    await _add(service, user, TransactionType.income, 999_999, income_cat, PaymentMethod.card, last_month)

    report_service = ReportService(TransactionRepository(session), TASHKENT)
    date_from, date_to = report_service.period_this_month()
    summary = await report_service.summary_for_period(user.id, "Bu oy", date_from, date_to)

    assert summary.income == 8_500_000
    assert summary.expense == 3_200_000
    assert summary.net == 5_300_000


async def test_category_totals_and_percentages(session: AsyncSession, user: User) -> None:
    service = TransactionService(session, TransactionRepository(session), CategoryRepository(session))
    categories = await CategoryRepository(session).list_for_user(user.id, CategoryType.expense)
    food = next(c for c in categories if c.name == "Oziq-ovqat")
    transport = next(c for c in categories if c.name == "Transport")

    now = datetime.datetime.now(TASHKENT)
    await _add(service, user, TransactionType.expense, 800_000, food, PaymentMethod.cash, now)
    await _add(service, user, TransactionType.expense, 200_000, transport, PaymentMethod.cash, now)

    report_service = ReportService(TransactionRepository(session), TASHKENT)
    breakdown = await report_service.expense_breakdown(user.id)

    totals = {item.category.name: item.amount for item in breakdown}
    assert totals["Oziq-ovqat"] == 800_000
    assert totals["Transport"] == 200_000

    percents = {item.category.name: item.percent for item in breakdown}
    assert percents["Oziq-ovqat"] == 80.0
    assert percents["Transport"] == 20.0


async def test_date_range_boundaries_are_respected(session: AsyncSession, user: User) -> None:
    service = TransactionService(session, TransactionRepository(session), CategoryRepository(session))
    expense_cat = (await CategoryRepository(session).list_for_user(user.id, CategoryType.expense))[0]

    today_start = datetime.datetime.now(TASHKENT).replace(hour=0, minute=0, second=0, microsecond=0)
    just_before_today = today_start - datetime.timedelta(minutes=1)
    just_after_today = today_start + datetime.timedelta(minutes=1)

    await _add(service, user, TransactionType.expense, 111, expense_cat, PaymentMethod.cash, just_before_today)
    await _add(service, user, TransactionType.expense, 222, expense_cat, PaymentMethod.cash, just_after_today)

    report_service = ReportService(TransactionRepository(session), TASHKENT)
    date_from, date_to = report_service.period_today()
    summary = await report_service.summary_for_period(user.id, "Bugun", date_from, date_to)

    assert summary.expense == 222
