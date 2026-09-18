from __future__ import annotations

import math

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers.shared import build_confirmation_text, get_transaction_service
from app.bot.keyboards.categories import CB_CATEGORY_PREFIX, categories_keyboard
from app.bot.keyboards.common import cancel_only_keyboard
from app.bot.keyboards.history import (
    CB_FILTER,
    CB_OPEN_PREFIX,
    CB_PAGE_PREFIX,
    delete_confirmation_keyboard,
    edit_field_keyboard,
    filter_category_keyboard,
    filter_type_keyboard,
    history_keyboard,
    transaction_detail_keyboard,
)
from app.bot.keyboards.main_menu import BTN_TRANSACTIONS
from app.bot.keyboards.payment import CB_PAYMENT_PREFIX, payment_method_keyboard
from app.bot.states.transaction_states import EditTransactionStates
from app.database.models import CategoryType, PaymentMethod, Transaction, TransactionType, User
from app.database.repositories.category_repo import CategoryRepository
from app.database.repositories.transaction_repo import TransactionFilter, TransactionRepository
from app.services.transaction_service import validate_amount
from app.utils.exceptions import AppError
from app.utils.formatting import format_amount

router = Router(name="history")

PAGE_SIZE = 8


def _build_filter(data: dict) -> TransactionFilter:
    type_ = TransactionType(data["filter_type"]) if data.get("filter_type") else None
    payment = PaymentMethod(data["filter_payment"]) if data.get("filter_payment") else None
    return TransactionFilter(
        type_=type_,
        category_id=data.get("filter_category_id"),
        payment_method=payment,
    )


def _list_text(transactions: list[Transaction]) -> str:
    if not transactions:
        return "📋 Tranzaksiyalar topilmadi."
    lines = ["📋 So'nggi tranzaksiyalar", ""]
    last_date = None
    for t in transactions:
        d = t.transaction_date.date()
        if d != last_date:
            if last_date is not None:
                lines.append("")
            lines.append(t.transaction_date.strftime("%d.%m"))
            last_date = d
        if t.type == TransactionType.transfer:
            arrow = "💵→💳" if t.transfer_from == PaymentMethod.cash else "💳→💵"
            lines.append(f"🔄 {format_amount(t.amount)} · {arrow}")
        else:
            icon = "➕" if t.type == TransactionType.income else "➖"
            cat_name = t.category.name if t.category else "-"
            pay_label = "💵 Naqd" if t.payment_method == PaymentMethod.cash else "💳 Karta"
            lines.append(f"{icon} {format_amount(t.amount)} · {cat_name} · {pay_label}")
    return "\n".join(lines)


async def _render_page(session: AsyncSession, db_user: User, data: dict, page: int) -> tuple[str, object]:
    f = _build_filter(data)
    repo = TransactionRepository(session)
    transactions, total = await repo.list_paginated(db_user.id, f, offset=page * PAGE_SIZE, limit=PAGE_SIZE)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    text = _list_text(transactions)
    keyboard = history_keyboard(transactions, page, total_pages)
    return text, keyboard


@router.message(F.text == BTN_TRANSACTIONS)
async def show_transactions(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    await state.clear()
    await state.update_data(page=0)
    data = await state.get_data()
    text, keyboard = await _render_page(session, db_user, data, 0)
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith(CB_PAGE_PREFIX))
async def change_page(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    page = int(callback.data.removeprefix(CB_PAGE_PREFIX))
    await state.update_data(page=page)
    data = await state.get_data()
    text, keyboard = await _render_page(session, db_user, data, page)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == CB_FILTER)
async def show_filter_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text("🔍 Filtr\n\nQuyidagilardan birini tanlang:", reply_markup=filter_type_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("txf_type:"))
async def filter_by_type(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    value = callback.data.removeprefix("txf_type:")
    await state.update_data(filter_type=value, page=0)
    data = await state.get_data()
    text, keyboard = await _render_page(session, db_user, data, 0)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer("Filtr qo'llandi")


@router.callback_query(F.data.startswith("txf_pay:"))
async def filter_by_payment(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    value = callback.data.removeprefix("txf_pay:")
    await state.update_data(filter_payment=value, page=0)
    data = await state.get_data()
    text, keyboard = await _render_page(session, db_user, data, 0)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer("Filtr qo'llandi")


@router.callback_query(F.data == "txf_cat_menu")
async def filter_category_menu(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    repo = CategoryRepository(session)
    income = await repo.list_for_user(db_user.id, CategoryType.income)
    expense = await repo.list_for_user(db_user.id, CategoryType.expense)
    await callback.message.edit_text(
        "📂 Kategoriyani tanlang:", reply_markup=filter_category_keyboard(income + expense)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("txf_cat:"))
async def filter_by_category(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    category_id = int(callback.data.removeprefix("txf_cat:"))
    await state.update_data(filter_category_id=category_id, page=0)
    data = await state.get_data()
    text, keyboard = await _render_page(session, db_user, data, 0)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer("Filtr qo'llandi")


@router.callback_query(F.data == "txf_clear")
async def clear_filter(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    await state.update_data(filter_type=None, filter_payment=None, filter_category_id=None, page=0)
    data = await state.get_data()
    text, keyboard = await _render_page(session, db_user, data, 0)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer("Filtr tozalandi")


def _transaction_detail_text(t: Transaction) -> str:
    if t.type == TransactionType.transfer:
        direction = "💵 Naqd → 💳 Karta" if t.transfer_from == PaymentMethod.cash else "💳 Karta → 💵 Naqd"
        fee = t.fee or 0
        lines = [
            "🔄 O'tkazma",
            "",
            direction,
            f"💰 Summa: {format_amount(t.amount)}",
            f"💸 Komissiya: {format_amount(fee)}",
            f"✅ Kiritildi: {format_amount(t.amount - fee)}",
            f"📅 Sana: {t.transaction_date.strftime('%d.%m.%Y %H:%M')}",
        ]
        return "\n".join(lines)
    return build_confirmation_text(t.type, t.amount, t.category, t.payment_method, t.note, t.transaction_date, saved=True)


@router.callback_query(F.data.startswith(CB_OPEN_PREFIX))
async def open_transaction(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    transaction_id = int(callback.data.removeprefix(CB_OPEN_PREFIX))
    service = get_transaction_service(session)
    t = await service.get_transaction(transaction_id, db_user.id)
    text = _transaction_detail_text(t)
    if t.type == TransactionType.transfer:
        await callback.message.edit_text(text, reply_markup=delete_confirmation_keyboard(t.id))
    else:
        await callback.message.edit_text(text, reply_markup=transaction_detail_keyboard(t.id))
    await callback.answer()


@router.callback_query(F.data.startswith("txdel:"))
async def ask_delete(callback: CallbackQuery) -> None:
    transaction_id = int(callback.data.removeprefix("txdel:"))
    await callback.message.edit_text(
        "🗑 Haqiqatan ham o'chirmoqchimisiz?", reply_markup=delete_confirmation_keyboard(transaction_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("txdelyes:"))
async def confirm_delete(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    transaction_id = int(callback.data.removeprefix("txdelyes:"))
    service = get_transaction_service(session)
    await service.delete_transaction(transaction_id, db_user.id)
    await callback.answer("✅ O'chirildi!")
    data = await state.get_data()
    page = data.get("page", 0)
    text, keyboard = await _render_page(session, db_user, data, page)
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("txedit:"))
async def edit_menu(callback: CallbackQuery) -> None:
    transaction_id = int(callback.data.removeprefix("txedit:"))
    await callback.message.edit_text("✏️ Nimani o'zgartirmoqchisiz?", reply_markup=edit_field_keyboard(transaction_id))
    await callback.answer()


@router.callback_query(F.data.startswith("txeditfield:"))
async def edit_field(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    _, transaction_id_str, field = callback.data.split(":")
    transaction_id = int(transaction_id_str)
    await state.update_data(edit_transaction_id=transaction_id)

    if field == "amount":
        await state.set_state(EditTransactionStates.waiting_new_amount)
        await callback.message.edit_text("Yangi summani kiriting:", reply_markup=cancel_only_keyboard())
    elif field == "category":
        service = get_transaction_service(session)
        t = await service.get_transaction(transaction_id, db_user.id)
        categories = await CategoryRepository(session).list_for_user(db_user.id, CategoryType(t.type.value))
        await state.set_state(EditTransactionStates.waiting_new_category)
        await callback.message.edit_text("Yangi kategoriyani tanlang:", reply_markup=categories_keyboard(categories))
    elif field == "payment":
        await state.set_state(EditTransactionStates.waiting_new_payment)
        await callback.message.edit_text("Yangi to'lov usulini tanlang:", reply_markup=payment_method_keyboard())
    elif field == "note":
        await state.set_state(EditTransactionStates.waiting_new_note)
        await callback.message.edit_text(
            "Yangi izohni kiriting.\nIzohni olib tashlash uchun '-' yuboring.",
            reply_markup=cancel_only_keyboard(),
        )
    await callback.answer()


async def _finish_edit(target, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    data = await state.get_data()
    transaction_id = data["edit_transaction_id"]
    await state.clear()
    service = get_transaction_service(session)
    t = await service.get_transaction(transaction_id, db_user.id)
    text = "✅ Yangilandi!\n\n" + _transaction_detail_text(t)
    keyboard = (
        delete_confirmation_keyboard(t.id) if t.type == TransactionType.transfer else transaction_detail_keyboard(t.id)
    )
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=keyboard)
        await target.answer()
    else:
        await target.answer(text, reply_markup=keyboard)


@router.message(EditTransactionStates.waiting_new_amount)
async def process_new_amount(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    try:
        amount = validate_amount(message.text or "")
    except AppError as exc:
        await message.answer(exc.user_message)
        return
    data = await state.get_data()
    service = get_transaction_service(session)
    await service.update_transaction(data["edit_transaction_id"], db_user.id, amount=amount)
    await _finish_edit(message, state, session, db_user)


@router.callback_query(F.data.startswith(CB_CATEGORY_PREFIX), EditTransactionStates.waiting_new_category)
async def process_new_category(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    category_id = int(callback.data.removeprefix(CB_CATEGORY_PREFIX))
    category = await CategoryRepository(session).get_by_id(category_id, db_user.id)
    if category is None or not category.is_active:
        await callback.answer("❌ Kategoriya topilmadi.", show_alert=True)
        return
    data = await state.get_data()
    service = get_transaction_service(session)
    await service.update_transaction(data["edit_transaction_id"], db_user.id, category_id=category.id)
    await _finish_edit(callback, state, session, db_user)


@router.callback_query(F.data.startswith(CB_PAYMENT_PREFIX), EditTransactionStates.waiting_new_payment)
async def process_new_payment(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    method = PaymentMethod(callback.data.removeprefix(CB_PAYMENT_PREFIX))
    data = await state.get_data()
    service = get_transaction_service(session)
    await service.update_transaction(data["edit_transaction_id"], db_user.id, payment_method=method)
    await _finish_edit(callback, state, session, db_user)


@router.message(EditTransactionStates.waiting_new_note)
async def process_new_note(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    raw = (message.text or "").strip()
    note = None if raw == "-" else raw[:512]
    data = await state.get_data()
    service = get_transaction_service(session)
    await service.update_transaction(data["edit_transaction_id"], db_user.id, note=note)
    await _finish_edit(message, state, session, db_user)
