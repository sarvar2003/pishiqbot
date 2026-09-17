from __future__ import annotations

import datetime
import enum

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base


class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"
    transfer = "transfer"


class PaymentMethod(str, enum.Enum):
    cash = "cash"
    card = "card"


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_user_date", "user_id", "transaction_date"),
        Index("ix_transactions_user_type", "user_id", "type"),
        Index("ix_transactions_user_payment", "user_id", "payment_method"),
        Index("ix_transactions_user_category", "user_id", "category_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[TransactionType] = mapped_column(
        SAEnum(TransactionType, name="transaction_type"), nullable=False
    )
    # Whole so'm. Never a float - all money math is integer arithmetic.
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Set for income/expense, NULL for transfers.
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=True
    )
    payment_method: Mapped[PaymentMethod | None] = mapped_column(
        SAEnum(PaymentMethod, name="payment_method"), nullable=True
    )

    # Set for transfers only, NULL for income/expense.
    transfer_from: Mapped[PaymentMethod | None] = mapped_column(
        SAEnum(PaymentMethod, name="payment_method_from"), nullable=True
    )
    transfer_to: Mapped[PaymentMethod | None] = mapped_column(
        SAEnum(PaymentMethod, name="payment_method_to"), nullable=True
    )

    note: Mapped[str | None] = mapped_column(String(512), nullable=True)
    transaction_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="transactions")  # noqa: F821
    category: Mapped["Category | None"] = relationship(back_populates="transactions")  # noqa: F821
