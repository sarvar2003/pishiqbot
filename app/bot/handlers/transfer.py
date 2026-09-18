from __future__ import annotations

import datetime

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers.shared import cancel_flow, get_transaction_service
from app.bot.keyboards.common import CB_BACK, CB_CANCEL, CB_CONFIRM, cancel_only_keyboard, confirmation_keyboard
from app.bot.keyboards.main_menu import BTN_TRANSFER, main_menu_keyboard
from app.bot.keyboards.transfer import (
    CB_TRANSFER_CARD_TO_CASH,
    CB_TRANSFER_CASH_TO_CARD,
    transfer_direction_keyboard,
)
from app.bot.states.transaction_states import TransferStates
from app.config import settings
from app.database.models import PaymentMethod, User
from app.services.transaction_service import calculate_transfer_fee, validate_amount
from app.utils.exceptions import AppError
from app.utils.formatting import format_amount

router = Router(name="transfer")

_DIRECTION_LABELS = {
    (PaymentMethod.cash, PaymentMethod.card): "💵 Naqd → 💳 Karta",
    (PaymentMethod.card, PaymentMethod.cash): "💳 Karta → 💵 Naqd",
}


def _transfer_preview_text(from_method: PaymentMethod, to_method: PaymentMethod, amount: int) -> str:
    fee = calculate_transfer_fee(amount)
    net = amount - fee
    return (
        f"{_DIRECTION_LABELS[(from_method, to_method)]}\n"
        f"💰 Summa: {format_amount(amount)}\n"
        f"💸 Komissiya (1%): {format_amount(fee)}\n"
        f"✅ Kiritiladi: {format_amount(net)}\n\n"
        "Saqlaymi?"
    )


def _transfer_saved_text(from_method: PaymentMethod, to_method: PaymentMethod, amount: int) -> str:
    fee = calculate_transfer_fee(amount)
    net = amount - fee
    return (
        "✅ O'tkazma saqlandi!\n\n"
        f"{_DIRECTION_LABELS[(from_method, to_method)]}\n"
        f"💰 Summa: {format_amount(amount)}\n"
        f"💸 Komissiya (1%): {format_amount(fee)}\n"
        f"✅ Kiritildi: {format_amount(net)}"
    )


@router.message(F.text == BTN_TRANSFER)
async def start_transfer(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(TransferStates.waiting_direction)
    await message.answer("🔄 Pul o'tkazish\n\nYo'nalishni tanlang:", reply_markup=transfer_direction_keyboard())


@router.callback_query(F.data.in_({CB_TRANSFER_CASH_TO_CARD, CB_TRANSFER_CARD_TO_CASH}), TransferStates.waiting_direction)
async def choose_direction(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data == CB_TRANSFER_CASH_TO_CARD:
        from_method, to_method = PaymentMethod.cash, PaymentMethod.card
    else:
        from_method, to_method = PaymentMethod.card, PaymentMethod.cash

    await state.update_data(from_method=from_method.value, to_method=to_method.value)
    await state.set_state(TransferStates.waiting_amount)
    await callback.message.edit_text(
        f"{_DIRECTION_LABELS[(from_method, to_method)]}\n\nSummani kiriting:",
        reply_markup=cancel_only_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == CB_BACK, TransferStates.waiting_amount)
async def amount_back(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(TransferStates.waiting_direction)
    await callback.message.edit_text(
        "🔄 Pul o'tkazish\n\nYo'nalishni tanlang:", reply_markup=transfer_direction_keyboard()
    )
    await callback.answer()


@router.message(TransferStates.waiting_amount)
async def process_transfer_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = validate_amount(message.text or "")
    except AppError as exc:
        await message.answer(exc.user_message)
        return

    data = await state.get_data()
    from_method = PaymentMethod(data["from_method"])
    to_method = PaymentMethod(data["to_method"])
    await state.update_data(amount=amount)
    await state.set_state(TransferStates.confirming)
    text = _transfer_preview_text(from_method, to_method, amount)
    await message.answer(text, reply_markup=confirmation_keyboard())


@router.callback_query(F.data == CB_BACK, TransferStates.confirming)
async def confirm_back(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    from_method = PaymentMethod(data["from_method"])
    to_method = PaymentMethod(data["to_method"])
    await state.set_state(TransferStates.waiting_amount)
    await callback.message.edit_text(
        f"{_DIRECTION_LABELS[(from_method, to_method)]}\n\nSummani kiriting:",
        reply_markup=cancel_only_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == CB_CONFIRM, TransferStates.confirming)
async def confirm_transfer(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    data = await state.get_data()
    from_method = PaymentMethod(data["from_method"])
    to_method = PaymentMethod(data["to_method"])
    amount = data["amount"]
    now = datetime.datetime.now(settings.zone_info)

    service = get_transaction_service(session)
    await service.add_transfer(
        user_id=db_user.id,
        amount=amount,
        from_method=from_method,
        to_method=to_method,
        transaction_date=now,
    )
    await state.clear()

    text = _transfer_saved_text(from_method, to_method, amount)
    await callback.message.edit_text(text)
    await callback.message.answer("Asosiy menyu:", reply_markup=main_menu_keyboard())
    await callback.answer("✅ Saqlandi!")


@router.callback_query(F.data == CB_CANCEL, StateFilter(TransferStates))
async def cancel_transfer(callback: CallbackQuery, state: FSMContext) -> None:
    await cancel_flow(callback, state)
