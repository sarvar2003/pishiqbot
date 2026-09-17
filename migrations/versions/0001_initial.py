"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-17

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("first_name", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    category_type = sa.Enum("income", "expense", name="category_type")
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("type", category_type, nullable=False),
        sa.Column("icon", sa.String(length=8), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "name", "type", name="uq_category_user_name_type"),
    )
    op.create_index("ix_categories_user_id", "categories", ["user_id"])

    transaction_type = sa.Enum("income", "expense", "transfer", name="transaction_type")
    payment_method = sa.Enum("cash", "card", name="payment_method")
    payment_method_from = sa.Enum("cash", "card", name="payment_method_from")
    payment_method_to = sa.Enum("cash", "card", name="payment_method_to")

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", transaction_type, nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("payment_method", payment_method, nullable=True),
        sa.Column("transfer_from", payment_method_from, nullable=True),
        sa.Column("transfer_to", payment_method_to, nullable=True),
        sa.Column("note", sa.String(length=512), nullable=True),
        sa.Column("transaction_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])
    op.create_index("ix_transactions_transaction_date", "transactions", ["transaction_date"])
    op.create_index("ix_transactions_user_date", "transactions", ["user_id", "transaction_date"])
    op.create_index("ix_transactions_user_type", "transactions", ["user_id", "type"])
    op.create_index("ix_transactions_user_payment", "transactions", ["user_id", "payment_method"])
    op.create_index("ix_transactions_user_category", "transactions", ["user_id", "category_id"])


def downgrade() -> None:
    op.drop_table("transactions")
    op.drop_table("categories")
    op.drop_table("users")

    sa.Enum(name="payment_method_to").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="payment_method_from").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="payment_method").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="transaction_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="category_type").drop(op.get_bind(), checkfirst=True)
