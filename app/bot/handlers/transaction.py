from __future__ import annotations

import datetime

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers.shared import (
    build_confirmation_text,
    cancel_flow,
    get_transaction_service,
)
from app.bot.keyboards.categories import CB_CATEGORY_PREFIX, categories_keyboard
from app.bot.keyboards.common import (
    CB_BACK,
    CB_CANCEL,
    CB_CHANGE_DATE,
    CB_CONFIRM,
    CB_SKIP,
    back_cancel_keyboard,
    cancel_only_keyboard,
    transaction_confirmation_keyboard,
)
from app.bot.keyboards.main_menu import BTN_EXPENSE, BTN_INCOME, main_menu_keyboard
from app.bot.keyboards.payment import CB_PAYMENT_PREFIX, payment_method_keyboard
from app.bot.states.transaction_states import TransactionStates
from app.config import settings
from app.database.models import CategoryType, PaymentMethod, TransactionType, User
from app.database.repositories.category_repo import CategoryRepository
from app.services.transaction_service import validate_amount
from app.utils.exceptions import AppError

router = Router(name="transaction")

_TYPE_EMOJI = {TransactionType.income: "➕", TransactionType.expense: "➖"}
_TYPE_TITLE = {TransactionType.income: "Kirim", TransactionType.expense: "Chiqim"}


def _amount_prompt(type_: TransactionType) -> str:
    return f"{_TYPE_EMOJI[type_]} {_TYPE_TITLE[type_]}\n\nSummani kiriting:"


async def _categories_for(session: AsyncSession, db_user: User, type_: TransactionType):
    repo = CategoryRepository(session)
    return await repo.list_for_user(db_user.id, CategoryType(type_.value))


@router.message(F.text.in_({BTN_INCOME, BTN_EXPENSE}))
async def start_add_transaction(message: Message, state: FSMContext) -> None:
    await state.clear()
    type_ = TransactionType.income if message.text == BTN_INCOME else TransactionType.expense
    await state.set_state(TransactionStates.waiting_amount)
    await state.update_data(type=type_.value)
    await message.answer(_amount_prompt(type_), reply_markup=cancel_only_keyboard())


@router.message(TransactionStates.waiting_amount)
async def process_amount(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    try:
        amount = validate_amount(message.text or "")
    except AppError as exc:
        await message.answer(exc.user_message)
        return

    data = await state.get_data()
    type_ = TransactionType(data["type"])
    await state.update_data(amount=amount)
    await state.set_state(TransactionStates.waiting_category)
    categories = await _categories_for(session, db_user, type_)
    await message.answer("Kategoriyani tanlang:", reply_markup=categories_keyboard(categories))


@router.callback_query(F.data == CB_BACK, TransactionStates.waiting_category)
async def category_back(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    type_ = TransactionType(data["type"])
    await state.set_state(TransactionStates.waiting_amount)
    await callback.message.edit_text(_amount_prompt(type_), reply_markup=cancel_only_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith(CB_CATEGORY_PREFIX), TransactionStates.waiting_category)
async def process_category(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User
) -> None:
    category_id = int(callback.data.removeprefix(CB_CATEGORY_PREFIX))
    category = await CategoryRepository(session).get_by_id(category_id, db_user.id)
    if category is None or not category.is_active:
        await callback.answer("❌ Kategoriya topilmadi.", show_alert=True)
        return
    await state.update_data(category_id=category.id)
    await state.set_state(TransactionStates.waiting_payment)
    await callback.message.edit_text("To'lov usulini tanlang:", reply_markup=payment_method_keyboard())
    await callback.answer()


@router.callback_query(F.data == CB_BACK, TransactionStates.waiting_payment)
async def payment_back(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User
) -> None:
    data = await state.get_data()
    type_ = TransactionType(data["type"])
    await state.set_state(TransactionStates.waiting_category)
    categories = await _categories_for(session, db_user, type_)
    await callback.message.edit_text("Kategoriyani tanlang:", reply_markup=categories_keyboard(categories))
    await callback.answer()


@router.callback_query(F.data.startswith(CB_PAYMENT_PREFIX), TransactionStates.waiting_payment)
async def process_payment(callback: CallbackQuery, state: FSMContext) -> None:
    method = PaymentMethod(callback.data.removeprefix(CB_PAYMENT_PREFIX))
    await state.update_data(payment_method=method.value)
    await state.set_state(TransactionStates.waiting_note)
    await callback.message.edit_text(
        "📝 Izoh yozing yoki o'tkazib yuboring.", reply_markup=back_cancel_keyboard(include_skip=True)
    )
    await callback.answer()


@router.callback_query(F.data == CB_BACK, TransactionStates.waiting_note)
async def note_back(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(TransactionStates.waiting_payment)
    await callback.message.edit_text("To'lov usulini tanlang:", reply_markup=payment_method_keyboard())
    await callback.answer()


async def _enter_confirming(state: FSMContext) -> None:
    data = await state.get_data()
    if "dt" not in data:
        now = datetime.datetime.now(settings.zone_info)
        await state.update_data(dt=now.isoformat())
    await state.set_state(TransactionStates.confirming)


async def _confirmation_text(state: FSMContext, session: AsyncSession, db_user: User) -> str:
    data = await state.get_data()
    category = await CategoryRepository(session).get_by_id(data["category_id"], db_user.id)
    dt = datetime.datetime.fromisoformat(data["dt"])
    return build_confirmation_text(
        TransactionType(data["type"]),
        data["amount"],
        category,
        PaymentMethod(data["payment_method"]),
        data.get("note"),
        dt,
        saved=False,
    )


@router.callback_query(F.data == CB_SKIP, TransactionStates.waiting_note)
async def note_skip(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    await state.update_data(note=None)
    await _enter_confirming(state)
    text = await _confirmation_text(state, session, db_user)
    await callback.message.edit_text(text, reply_markup=transaction_confirmation_keyboard())
    await callback.answer()


@router.message(TransactionStates.waiting_note)
async def note_entered(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    note = (message.text or "").strip()[:512] or None
    await state.update_data(note=note)
    await _enter_confirming(state)
    text = await _confirmation_text(state, session, db_user)
    await message.answer(text, reply_markup=transaction_confirmation_keyboard())


@router.callback_query(F.data == CB_BACK, TransactionStates.confirming)
async def confirm_back(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(TransactionStates.waiting_note)
    await callback.message.edit_text(
        "📝 Izoh yozing yoki o'tkazib yuboring.", reply_markup=back_cancel_keyboard(include_skip=True)
    )
    await callback.answer()


@router.callback_query(F.data == CB_CHANGE_DATE, TransactionStates.confirming)
async def change_date(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(TransactionStates.waiting_datetime)
    await callback.message.edit_text(
        "📅 Sana va vaqtni kiriting.\n"
        "Format: KK.OO.YYYY SS:DD\n"
        "Masalan: 17.09.2026 14:30\n\n"
        "Joriy sanani qoldirish uchun pastdagi tugmani bosing.",
        reply_markup=back_cancel_keyboard(include_skip=True),
    )
    await callback.answer()


async def _back_to_confirming(target_message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    await state.set_state(TransactionStates.confirming)
    text = await _confirmation_text(state, session, db_user)
    await target_message.edit_text(text, reply_markup=transaction_confirmation_keyboard())


@router.callback_query(F.data.in_({CB_BACK, CB_SKIP}), TransactionStates.waiting_datetime)
async def datetime_skip_or_back(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User
) -> None:
    await _back_to_confirming(callback.message, state, session, db_user)
    await callback.answer()


@router.message(TransactionStates.waiting_datetime)
async def datetime_entered(
    message: Message, state: FSMContext, session: AsyncSession, db_user: User
) -> None:
    try:
        parsed = datetime.datetime.strptime((message.text or "").strip(), "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer(
            "❌ Format noto'g'ri. Masalan: 17.09.2026 14:30\nQaytadan kiriting yoki tugmalardan foydalaning."
        )
        return
    localized = parsed.replace(tzinfo=settings.zone_info)
    await state.update_data(dt=localized.isoformat())
    await state.set_state(TransactionStates.confirming)
    text = await _confirmation_text(state, session, db_user)
    await message.answer(text, reply_markup=transaction_confirmation_keyboard())


@router.callback_query(F.data == CB_CONFIRM, TransactionStates.confirming)
async def confirm_save(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    data = await state.get_data()
    category = await CategoryRepository(session).get_by_id(data["category_id"], db_user.id)
    dt = datetime.datetime.fromisoformat(data["dt"])
    type_ = TransactionType(data["type"])
    payment_method = PaymentMethod(data["payment_method"])

    service = get_transaction_service(session)
    await service.add_income_or_expense(
        user_id=db_user.id,
        type_=type_,
        amount=data["amount"],
        category=category,
        payment_method=payment_method,
        transaction_date=dt,
        note=data.get("note"),
    )
    await state.clear()

    text = build_confirmation_text(type_, data["amount"], category, payment_method, data.get("note"), dt, saved=True)
    await callback.message.edit_text(text)
    await callback.message.answer("Asosiy menyu:", reply_markup=main_menu_keyboard())
    await callback.answer("✅ Saqlandi!")


@router.callback_query(F.data == CB_CANCEL, StateFilter(TransactionStates))
async def cancel_transaction(callback: CallbackQuery, state: FSMContext) -> None:
    await cancel_flow(callback, state)
