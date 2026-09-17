from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.main_menu import BTN_BALANCE
from app.database.models import User
from app.database.repositories.transaction_repo import TransactionRepository
from app.services.balance_service import BalanceService
from app.utils.formatting import format_amount

router = Router(name="balance")


@router.message(F.text == BTN_BALANCE)
async def show_balance(message: Message, session: AsyncSession, db_user: User) -> None:
    service = BalanceService(TransactionRepository(session))
    balance = await service.get_balance(db_user.id)

    text = (
        "💰 Balans\n\n"
        f"💵 Naqd:   {format_amount(balance.cash)}\n"
        f"💳 Karta:  {format_amount(balance.card)}\n"
        "━━━━━━━━━━━━━━━━\n"
        f"💰 Jami:   {format_amount(balance.total)}"
    )
    await message.answer(text)
