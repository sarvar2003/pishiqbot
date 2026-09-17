from __future__ import annotations

import datetime
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from app.database.models import Category, TransactionType
from app.database.repositories.transaction_repo import TransactionRepository
from app.utils.datetime_utils import (
    end_of_day,
    start_of_day,
    start_of_month,
    start_of_next_month,
    start_of_previous_month,
    start_of_week,
)


@dataclass(frozen=True)
class PeriodSummary:
    label: str
    income: int
    expense: int

    @property
    def net(self) -> int:
        return self.income - self.expense


@dataclass(frozen=True)
class CategoryBreakdownItem:
    category: Category
    amount: int
    percent: float


class ReportService:
    def __init__(self, transaction_repo: TransactionRepository, tz: ZoneInfo):
        self.transaction_repo = transaction_repo
        self.tz = tz

    def _now(self) -> datetime.datetime:
        return datetime.datetime.now(self.tz)

    def period_today(self) -> tuple[datetime.datetime, datetime.datetime]:
        now = self._now()
        return start_of_day(now), end_of_day(now)

    def period_yesterday(self) -> tuple[datetime.datetime, datetime.datetime]:
        now = self._now()
        yesterday = start_of_day(now) - datetime.timedelta(days=1)
        return yesterday, start_of_day(now)

    def period_this_week(self) -> tuple[datetime.datetime, datetime.datetime]:
        now = self._now()
        return start_of_week(now), end_of_day(now)

    def period_this_month(self) -> tuple[datetime.datetime, datetime.datetime]:
        now = self._now()
        return start_of_month(now), start_of_next_month(now)

    def period_previous_month(self) -> tuple[datetime.datetime, datetime.datetime]:
        now = self._now()
        return start_of_previous_month(now), start_of_month(now)

    async def summary_for_period(
        self, user_id: int, label: str, date_from: datetime.datetime, date_to: datetime.datetime
    ) -> PeriodSummary:
        income = await self.transaction_repo.sum_amount(
            user_id, TransactionType.income, date_from=date_from, date_to=date_to
        )
        expense = await self.transaction_repo.sum_amount(
            user_id, TransactionType.expense, date_from=date_from, date_to=date_to
        )
        return PeriodSummary(label=label, income=income, expense=expense)

    async def today_and_month_summary(self, user_id: int) -> tuple[PeriodSummary, PeriodSummary]:
        today_from, today_to = self.period_today()
        month_from, month_to = self.period_this_month()
        today = await self.summary_for_period(user_id, "Bugun", today_from, today_to)
        month = await self.summary_for_period(user_id, "Bu oy", month_from, month_to)
        return today, month

    async def expense_breakdown(
        self,
        user_id: int,
        date_from: datetime.datetime | None = None,
        date_to: datetime.datetime | None = None,
    ) -> list[CategoryBreakdownItem]:
        totals = await self.transaction_repo.expense_totals_by_category(user_id, date_from, date_to)
        grand_total = sum(amount for _, amount in totals)
        result = []
        for category, amount in totals:
            percent = (amount / grand_total * 100) if grand_total > 0 else 0.0
            result.append(CategoryBreakdownItem(category=category, amount=amount, percent=percent))
        return result
