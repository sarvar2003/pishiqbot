from __future__ import annotations

import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database.models import Category, PaymentMethod, Transaction, TransactionType


class TransactionFilter:
    def __init__(
        self,
        type_: TransactionType | None = None,
        category_id: int | None = None,
        payment_method: PaymentMethod | None = None,
        date_from: datetime.datetime | None = None,
        date_to: datetime.datetime | None = None,
    ):
        self.type_ = type_
        self.category_id = category_id
        self.payment_method = payment_method
        self.date_from = date_from
        self.date_to = date_to


class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _apply_filters(self, stmt: Select, user_id: int, f: TransactionFilter | None) -> Select:
        stmt = stmt.where(Transaction.user_id == user_id)
        if f is None:
            return stmt
        if f.type_ is not None:
            stmt = stmt.where(Transaction.type == f.type_)
        if f.category_id is not None:
            stmt = stmt.where(Transaction.category_id == f.category_id)
        if f.payment_method is not None:
            stmt = stmt.where(
                (Transaction.payment_method == f.payment_method)
                | (Transaction.transfer_from == f.payment_method)
                | (Transaction.transfer_to == f.payment_method)
            )
        if f.date_from is not None:
            stmt = stmt.where(Transaction.transaction_date >= f.date_from)
        if f.date_to is not None:
            stmt = stmt.where(Transaction.transaction_date < f.date_to)
        return stmt

    async def create(self, **kwargs) -> Transaction:
        transaction = Transaction(**kwargs)
        self.session.add(transaction)
        await self.session.flush()
        return transaction

    async def get_by_id(self, transaction_id: int, user_id: int) -> Transaction | None:
        result = await self.session.execute(
            select(Transaction)
            .options(joinedload(Transaction.category))
            .where(Transaction.id == transaction_id, Transaction.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update(self, transaction: Transaction, **fields) -> Transaction:
        for key, value in fields.items():
            setattr(transaction, key, value)
        await self.session.flush()
        return transaction

    async def delete(self, transaction: Transaction) -> None:
        await self.session.delete(transaction)
        await self.session.flush()

    async def list_paginated(
        self,
        user_id: int,
        f: TransactionFilter | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> tuple[list[Transaction], int]:
        base = select(Transaction).where(Transaction.user_id == user_id)
        base = self._apply_filters(base, user_id, f)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            self._apply_filters(
                select(Transaction).options(joinedload(Transaction.category)), user_id, f
            )
            .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def sum_amount(
        self,
        user_id: int,
        type_: TransactionType,
        payment_method: PaymentMethod | None = None,
        date_from: datetime.datetime | None = None,
        date_to: datetime.datetime | None = None,
    ) -> int:
        stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id, Transaction.type == type_
        )
        if payment_method is not None:
            stmt = stmt.where(Transaction.payment_method == payment_method)
        if date_from is not None:
            stmt = stmt.where(Transaction.transaction_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Transaction.transaction_date < date_to)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def sum_transfers(
        self, user_id: int, direction_field: str, payment_method: PaymentMethod, net: bool = False
    ) -> int:
        """Sums transfer amounts in the given direction. `net=True` subtracts the
        commission fee - use it for transfer_to, since the receiving side only
        gets amount - fee (the source side still loses the full amount)."""
        column = getattr(Transaction, direction_field)
        amount_expr = (
            Transaction.amount - func.coalesce(Transaction.fee, 0) if net else Transaction.amount
        )
        stmt = select(func.coalesce(func.sum(amount_expr), 0)).where(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.transfer,
            column == payment_method,
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def expense_totals_by_category(
        self,
        user_id: int,
        date_from: datetime.datetime | None = None,
        date_to: datetime.datetime | None = None,
    ) -> list[tuple[Category, int]]:
        stmt = (
            select(Category, func.coalesce(func.sum(Transaction.amount), 0))
            .join(Transaction, Transaction.category_id == Category.id)
            .where(Transaction.user_id == user_id, Transaction.type == TransactionType.expense)
        )
        if date_from is not None:
            stmt = stmt.where(Transaction.transaction_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Transaction.transaction_date < date_to)
        stmt = stmt.group_by(Category.id).order_by(func.sum(Transaction.amount).desc())
        result = await self.session.execute(stmt)
        return [(row[0], int(row[1])) for row in result.all()]
