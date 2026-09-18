"""add transfer commission fee column

Revision ID: 0002_transfer_fee
Revises: 0001_initial
Create Date: 2026-09-18

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_transfer_fee"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("fee", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("transactions", "fee")
