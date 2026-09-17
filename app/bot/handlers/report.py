from __future__ import annotations

import datetime

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers.shared import cancel_flow
from app.bot.keyboards.common import CB_CANCEL, cancel_only_keyboard
from app.bot.keyboards.main_menu import BTN_REPORT
from app.bot.keyboards.reports import (
    CB_PERIOD_PREFIX,
    PERIOD_MONTH,
    PERIOD_PREV_MONTH,
    PERIOD_TODAY,
    PERIOD_WEEK,
    PERIOD_YESTERDAY,
    report_period_keyboard,
)
from app.bot.states.transaction_states import ReportStates
from app.config import settings
from app.database.models import User
from app.database.repositories.transaction_repo import TransactionRepository
from app.services.report_service import CategoryBreakdownItem, PeriodSummary, ReportService
from app.utils.datetime_utils import parse_date_ddmmyyyy
from app.utils.formatting import format_amount, format_signed_amount

router = Router(name="report")

_PERIOD_LABELS = {
    PERIOD_TODAY: "Bugun",
    PERIOD_YESTERDAY: "Kecha",
    PERIOD_WEEK: "Shu hafta",
    PERIOD_MONTH: "Bu oy",
    PERIOD_PREV_MONTH: "O'tgan oy",
}


def _report_service(session: AsyncSession) -> ReportService:
    return ReportService(TransactionRepository(session), settings.zone_info)


def _period_text(summary: PeriodSummary) -> str:
    return (
        f"{summary.label}\n"
        "━━━━━━━━━━━━━━━━\n"
        f"📈 Kirim: {format_amount(summary.income)}\n"
        f"📉 Chiqim: {format_amount(summary.expense)}\n"
        f"💰 Sof o'zgarish: {format_signed_amount(summary.net)}"
    )


def _breakdown_text(items: list[CategoryBreakdownItem]) -> str:
    if not items:
        return "Bu davrda chiqimlar yo'q."
    lines = ["📊 Chiqimlar", ""]
    for item in items:
        lines.append(f"{item.category.display_name}   {format_amount(item.amount)} ({item.percent:.0f}%)")
    return "\n".join(lines)


@router.message(F.text == BTN_REPORT)
async def show_report_menu(message: Message, session: AsyncSession, db_user: User) -> None:
    service = _report_service(session)
    today, month = await service.today_and_month_summary(db_user.id)
    text = "📊 Hisobot\n\n" + _period_text(today) + "\n\n" + _period_text(month)
    await message.answer(text, reply_markup=report_period_keyboard())


async def _period_range(service: ReportService, key: str) -> tuple[str, datetime.datetime, datetime.datetime]:
    if key == PERIOD_TODAY:
        return _PERIOD_LABELS[key], *service.period_today()
    if key == PERIOD_YESTERDAY:
        return _PERIOD_LABELS[key], *service.period_yesterday()
    if key == PERIOD_WEEK:
        return _PERIOD_LABELS[key], *service.period_this_week()
    if key == PERIOD_MONTH:
        return _PERIOD_LABELS[key], *service.period_this_month()
    if key == PERIOD_PREV_MONTH:
        return _PERIOD_LABELS[key], *service.period_previous_month()
    raise ValueError(f"Unknown period key: {key}")


@router.callback_query(F.data.startswith(CB_PERIOD_PREFIX))
async def choose_period(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    key = callback.data.removeprefix(CB_PERIOD_PREFIX)
    service = _report_service(session)

    if key == "custom":
        await state.set_state(ReportStates.waiting_custom_date_from)
        await callback.message.edit_text(
            "📅 Boshlanish sanasini kiriting (KK.OO.YYYY):", reply_markup=cancel_only_keyboard()
        )
        await callback.answer()
        return

    label, date_from, date_to = await _period_range(service, key)
    summary = await service.summary_for_period(db_user.id, label, date_from, date_to)
    breakdown = await service.expense_breakdown(db_user.id, date_from, date_to)
    text = _period_text(summary) + "\n\n" + _breakdown_text(breakdown)
    await callback.message.edit_text(text, reply_markup=report_period_keyboard())
    await callback.answer()


@router.message(ReportStates.waiting_custom_date_from)
async def custom_date_from(message: Message, state: FSMContext) -> None:
    date = parse_date_ddmmyyyy(message.text or "")
    if date is None:
        await message.answer("❌ Format noto'g'ri. Masalan: 01.09.2026")
        return
    await state.update_data(date_from=date.isoformat())
    await state.set_state(ReportStates.waiting_custom_date_to)
    await message.answer("📅 Tugash sanasini kiriting (KK.OO.YYYY):", reply_markup=cancel_only_keyboard())


@router.message(ReportStates.waiting_custom_date_to)
async def custom_date_to(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    date_to = parse_date_ddmmyyyy(message.text or "")
    if date_to is None:
        await message.answer("❌ Format noto'g'ri. Masalan: 30.09.2026")
        return

    data = await state.get_data()
    date_from = datetime.date.fromisoformat(data["date_from"])
    if date_to < date_from:
        await message.answer("❌ Tugash sanasi boshlanish sanasidan oldin bo'lishi mumkin emas.")
        return

    tz = settings.zone_info
    dt_from = datetime.datetime.combine(date_from, datetime.time.min, tzinfo=tz)
    dt_to = datetime.datetime.combine(date_to, datetime.time.min, tzinfo=tz) + datetime.timedelta(days=1)

    await state.clear()
    service = _report_service(session)
    label = f"{date_from.strftime('%d.%m.%Y')} - {date_to.strftime('%d.%m.%Y')}"
    summary = await service.summary_for_period(db_user.id, label, dt_from, dt_to)
    breakdown = await service.expense_breakdown(db_user.id, dt_from, dt_to)
    text = _period_text(summary) + "\n\n" + _breakdown_text(breakdown)
    await message.answer(text, reply_markup=report_period_keyboard())


@router.callback_query(F.data == CB_CANCEL, StateFilter(ReportStates))
async def cancel_report(callback: CallbackQuery, state: FSMContext) -> None:
    await cancel_flow(callback, state)
