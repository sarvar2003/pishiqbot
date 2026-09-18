from __future__ import annotations

from dataclasses import dataclass

from app.database.models import PaymentMethod, TransactionType
from app.database.repositories.transaction_repo import TransactionRepository


@dataclass(frozen=True)
class Balance:
    cash: int
    card: int

    @property
    def total(self) -> int:
        return self.cash + self.card


class BalanceService:
    """Computes balances from transaction history - never stores a mutable balance."""

    def __init__(self, transaction_repo: TransactionRepository):
        self.transaction_repo = transaction_repo

    async def _balance_for(self, user_id: int, method: PaymentMethod) -> int:
        income = await self.transaction_repo.sum_amount(
            user_id, TransactionType.income, payment_method=method
        )
        expense = await self.transaction_repo.sum_amount(
            user_id, TransactionType.expense, payment_method=method
        )
        # transfer_to only receives amount - commission fee; transfer_from loses the full amount.
        transfers_in = await self.transaction_repo.sum_transfers(user_id, "transfer_to", method, net=True)
        transfers_out = await self.transaction_repo.sum_transfers(user_id, "transfer_from", method)
        return income - expense + transfers_in - transfers_out

    async def get_balance(self, user_id: int) -> Balance:
        cash = await self._balance_for(user_id, PaymentMethod.cash)
        card = await self._balance_for(user_id, PaymentMethod.card)
        return Balance(cash=cash, card=card)
