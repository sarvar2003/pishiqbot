from __future__ import annotations

import datetime

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.main_menu import main_menu_keyboard
from app.bot.keyboards.payment import PAYMENT_LABELS
from app.database.models import Category, PaymentMethod, TransactionType
from app.database.repositories.category_repo import CategoryRepository
from app.database.repositories.transaction_repo import TransactionRepository
from app.services.category_service import CategoryService
from app.services.transaction_service import TransactionService
from app.utils.formatting import format_amount, format_datetime

CANCELLED_TEXT = "❌ Amal bekor qilindi."


def get_transaction_service(session: AsyncSession) -> TransactionService:
    return TransactionService(session, TransactionRepository(session), CategoryRepository(session))


def get_category_service(session: AsyncSession) -> CategoryService:
    return CategoryService(session, CategoryRepository(session))

TYPE_LABELS = {
    TransactionType.income: "Kirim",
    TransactionType.expense: "Chiqim",
}


async def cancel_flow(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if callback.message is not None:
        await callback.message.edit_text(CANCELLED_TEXT)
        await callback.message.answer("Asosiy menyu:", reply_markup=main_menu_keyboard())
    await callback.answer()


def build_confirmation_text(
    type_: TransactionType,
    amount: int,
    category: Category,
    payment_method: PaymentMethod,
    note: str | None,
    dt: datetime.datetime,
    saved: bool,
) -> str:
    emoji = "➕" if type_ == TransactionType.income else "➖"
    label = TYPE_LABELS[type_]
    header = f"✅ {label} saqlandi!" if saved else f"{emoji} {label} - tekshiring"
    lines = [
        header,
        "",
        f"💰 Summa: {format_amount(amount)}",
        f"📂 Kategoriya: {category.display_name}",
        f"💳 To'lov: {PAYMENT_LABELS[payment_method].split(' ', 1)[1]}",
        f"📅 Sana: {format_datetime(dt)}",
    ]
    if note:
        lines.append(f"📝 Izoh: {note}")
    if not saved:
        lines.append("")
        lines.append("Saqlaymi?")
    return "\n".join(lines)
