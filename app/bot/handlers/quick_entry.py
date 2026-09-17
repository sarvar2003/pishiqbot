from __future__ import annotations

import datetime
import re

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers.shared import build_confirmation_text, cancel_flow, get_transaction_service
from app.bot.keyboards.categories import CB_CATEGORY_PREFIX, categories_keyboard
from app.bot.keyboards.common import CB_BACK, CB_CANCEL
from app.bot.keyboards.main_menu import main_menu_keyboard
from app.bot.keyboards.payment import CB_PAYMENT_PREFIX, payment_method_keyboard
from app.bot.states.transaction_states import QuickEntryStates
from app.config import settings
from app.database.models import Category, CategoryType, PaymentMethod, TransactionType, User
from app.database.repositories.category_repo import CategoryRepository
from app.services.quick_parser import parse_quick_entry

router = Router(name="quick_entry")

_LOOKS_LIKE_QUICK_ENTRY = re.compile(r"^\s*[+\-]\s*\d")


async def _save_and_report(
    message: Message,
    session: AsyncSession,
    db_user: User,
    type_: TransactionType,
    amount: int,
    category: Category,
    payment_method: PaymentMethod,
    note: str | None,
) -> None:
    now = datetime.datetime.now(settings.zone_info)
    service = get_transaction_service(session)
    await service.add_income_or_expense(
        user_id=db_user.id,
        type_=type_,
        amount=amount,
        category=category,
        payment_method=payment_method,
        transaction_date=now,
        note=note,
    )
    text = build_confirmation_text(type_, amount, category, payment_method, note, now, saved=True)
    await message.answer(text, reply_markup=main_menu_keyboard())


@router.message(F.text.regexp(_LOOKS_LIKE_QUICK_ENTRY), StateFilter(None))
async def handle_quick_entry(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    text = message.text or ""
    sign_type = TransactionType.income if text.strip().startswith("+") else TransactionType.expense
    categories = await CategoryRepository(session).list_for_user(db_user.id, CategoryType(sign_type.value))

    result = parse_quick_entry(text, categories)
    if result is None:
        await message.answer(
            "🤔 Tez kiritish formatini tanib bo'lmadi.\n\n"
            "Namuna: - 150000 oziq-ovqat karta\nyoki: + 500000 freelance karta"
        )
        return

    if result.amount_error:
        await message.answer(result.amount_error)
        return

    if result.matched_category is None:
        await state.update_data(
            qe_amount=result.amount,
            qe_type=result.type.value,
            qe_payment=result.payment_method.value if result.payment_method else None,
            qe_note=result.note,
        )
        await state.set_state(QuickEntryStates.waiting_category_choice)
        hint = (
            f"🤔 Kategoriya bir nechta mos keldi: '{result.category_query}'."
            if result.category_ambiguous
            else f"🤔 Kategoriya topilmadi: '{result.category_query}'."
        )
        await message.answer(f"{hint}\nTanlang:", reply_markup=categories_keyboard(categories))
        return

    if result.payment_method is None:
        await state.update_data(
            qe_amount=result.amount,
            qe_type=result.type.value,
            qe_category_id=result.matched_category.id,
            qe_note=result.note,
        )
        await state.set_state(QuickEntryStates.waiting_payment_choice)
        await message.answer("To'lov usulini tanlang:", reply_markup=payment_method_keyboard())
        return

    await _save_and_report(
        message, session, db_user, result.type, result.amount, result.matched_category, result.payment_method, result.note
    )


@router.callback_query(F.data.startswith(CB_CATEGORY_PREFIX), QuickEntryStates.waiting_category_choice)
async def quick_entry_category_chosen(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User
) -> None:
    category_id = int(callback.data.removeprefix(CB_CATEGORY_PREFIX))
    category = await CategoryRepository(session).get_by_id(category_id, db_user.id)
    if category is None or not category.is_active:
        await callback.answer("❌ Kategoriya topilmadi.", show_alert=True)
        return

    data = await state.get_data()
    type_ = TransactionType(data["qe_type"])
    amount = data["qe_amount"]
    note = data.get("qe_note")
    payment_raw = data.get("qe_payment")

    if payment_raw is None:
        await state.update_data(qe_category_id=category.id)
        await state.set_state(QuickEntryStates.waiting_payment_choice)
        await callback.message.edit_text("To'lov usulini tanlang:", reply_markup=payment_method_keyboard())
        await callback.answer()
        return

    await state.clear()
    await callback.message.delete()
    await _save_and_report(callback.message, session, db_user, type_, amount, category, PaymentMethod(payment_raw), note)
    await callback.answer()


@router.callback_query(F.data.startswith(CB_PAYMENT_PREFIX), QuickEntryStates.waiting_payment_choice)
async def quick_entry_payment_chosen(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User
) -> None:
    method = PaymentMethod(callback.data.removeprefix(CB_PAYMENT_PREFIX))
    data = await state.get_data()
    type_ = TransactionType(data["qe_type"])
    amount = data["qe_amount"]
    note = data.get("qe_note")
    category = await CategoryRepository(session).get_by_id(data["qe_category_id"], db_user.id)

    await state.clear()
    await callback.message.delete()
    await _save_and_report(callback.message, session, db_user, type_, amount, category, method, note)
    await callback.answer()


@router.callback_query(F.data.in_({CB_CANCEL, CB_BACK}), StateFilter(QuickEntryStates))
async def cancel_quick_entry(callback: CallbackQuery, state: FSMContext) -> None:
    await cancel_flow(callback, state)
