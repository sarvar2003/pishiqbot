from __future__ import annotations

import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Category, PaymentMethod, Transaction, TransactionType
from app.database.repositories.category_repo import CategoryRepository
from app.database.repositories.transaction_repo import TransactionRepository
from app.utils.exceptions import InvalidAmountError, NotFoundError

MAX_AMOUNT = 999_999_999_999

# Naqd<->karta o'tkazmalar uchun komissiya - O'zbekistonda naqd/karta almashtirishda
# odatiy amaliyot. transfer_from full amount ni yo'qotadi, transfer_to amount - fee oladi.
TRANSFER_COMMISSION_PERCENT = 1


def calculate_transfer_fee(amount: int, percent: int = TRANSFER_COMMISSION_PERCENT) -> int:
    """Integer-only, round-half-up commission: fee = round(amount * percent / 100)."""
    return (amount * percent + 50) // 100


def validate_amount(raw: str) -> int:
    """Parse and validate a user-provided amount string. Raises InvalidAmountError on any problem."""
    cleaned = raw.strip().replace(" ", "").replace("'", "").replace(",", "")
    if not cleaned:
        raise InvalidAmountError("❌ Summani kiriting.")
    if not cleaned.lstrip("-").isdigit():
        raise InvalidAmountError("❌ Summa noto'g'ri. Faqat raqam kiriting, masalan: 150000")
    amount = int(cleaned)
    if amount == 0:
        raise InvalidAmountError("❌ Summa noldan katta bo'lishi kerak.")
    if amount < 0:
        raise InvalidAmountError("❌ Summa manfiy bo'lishi mumkin emas.")
    if amount > MAX_AMOUNT:
        raise InvalidAmountError("❌ Summa juda katta.")
    return amount


class TransactionService:
    def __init__(self, session: AsyncSession, transaction_repo: TransactionRepository, category_repo: CategoryRepository):
        self.session = session
        self.transaction_repo = transaction_repo
        self.category_repo = category_repo

    async def add_income_or_expense(
        self,
        user_id: int,
        type_: TransactionType,
        amount: int,
        category: Category,
        payment_method: PaymentMethod,
        transaction_date: datetime.datetime,
        note: str | None = None,
    ) -> Transaction:
        if amount <= 0:
            raise InvalidAmountError("❌ Summa noldan katta bo'lishi kerak.")
        transaction = await self.transaction_repo.create(
            user_id=user_id,
            type=type_,
            amount=amount,
            category_id=category.id,
            payment_method=payment_method,
            note=note,
            transaction_date=transaction_date,
        )
        await self.session.commit()
        return transaction

    async def add_transfer(
        self,
        user_id: int,
        amount: int,
        from_method: PaymentMethod,
        to_method: PaymentMethod,
        transaction_date: datetime.datetime,
        note: str | None = None,
    ) -> Transaction:
        if amount <= 0:
            raise InvalidAmountError("❌ Summa noldan katta bo'lishi kerak.")
        if from_method == to_method:
            raise InvalidAmountError("❌ Bir xil to'lov usuliga o'tkazib bo'lmaydi.")
        fee = calculate_transfer_fee(amount)
        transaction = await self.transaction_repo.create(
            user_id=user_id,
            type=TransactionType.transfer,
            amount=amount,
            fee=fee,
            transfer_from=from_method,
            transfer_to=to_method,
            note=note,
            transaction_date=transaction_date,
        )
        await self.session.commit()
        return transaction

    async def get_transaction(self, transaction_id: int, user_id: int) -> Transaction:
        transaction = await self.transaction_repo.get_by_id(transaction_id, user_id)
        if transaction is None:
            raise NotFoundError("❌ Tranzaksiya topilmadi.")
        return transaction

    async def update_transaction(self, transaction_id: int, user_id: int, **fields) -> Transaction:
        transaction = await self.get_transaction(transaction_id, user_id)
        amount = fields.get("amount")
        if amount is not None and amount <= 0:
            raise InvalidAmountError("❌ Summa noldan katta bo'lishi kerak.")
        await self.transaction_repo.update(transaction, **fields)
        await self.session.commit()
        return transaction

    async def delete_transaction(self, transaction_id: int, user_id: int) -> None:
        transaction = await self.get_transaction(transaction_id, user_id)
        await self.transaction_repo.delete(transaction)
        await self.session.commit()
