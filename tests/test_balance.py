from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import CategoryType, PaymentMethod, TransactionType, User
from app.database.repositories.category_repo import CategoryRepository
from app.database.repositories.transaction_repo import TransactionRepository
from app.services.balance_service import BalanceService
from app.services.transaction_service import TransactionService
from tests.conftest import dt


async def _setup(session: AsyncSession, user: User) -> TransactionService:
    return TransactionService(session, TransactionRepository(session), CategoryRepository(session))


async def test_cash_balance_from_income_and_expense(session: AsyncSession, user: User) -> None:
    service = await _setup(session, user)
    income_cat = (await CategoryRepository(session).list_for_user(user.id, CategoryType.income))[0]
    expense_cat = (await CategoryRepository(session).list_for_user(user.id, CategoryType.expense))[0]

    await service.add_income_or_expense(
        user_id=user.id, type_=TransactionType.income, amount=1_000_000,
        category=income_cat, payment_method=PaymentMethod.cash, transaction_date=dt(),
    )
    await service.add_income_or_expense(
        user_id=user.id, type_=TransactionType.expense, amount=200_000,
        category=expense_cat, payment_method=PaymentMethod.cash, transaction_date=dt(),
    )

    balance = await BalanceService(TransactionRepository(session)).get_balance(user.id)
    assert balance.cash == 800_000


async def test_card_balance_from_income_and_expense(session: AsyncSession, user: User) -> None:
    service = await _setup(session, user)
    income_cat = (await CategoryRepository(session).list_for_user(user.id, CategoryType.income))[0]
    expense_cat = (await CategoryRepository(session).list_for_user(user.id, CategoryType.expense))[0]

    await service.add_income_or_expense(
        user_id=user.id, type_=TransactionType.income, amount=4_000_000,
        category=income_cat, payment_method=PaymentMethod.card, transaction_date=dt(),
    )
    await service.add_income_or_expense(
        user_id=user.id, type_=TransactionType.expense, amount=750_000,
        category=expense_cat, payment_method=PaymentMethod.card, transaction_date=dt(),
    )

    balance = await BalanceService(TransactionRepository(session)).get_balance(user.id)
    assert balance.card == 3_250_000


async def test_total_balance_is_cash_plus_card(session: AsyncSession, user: User) -> None:
    service = await _setup(session, user)
    income_cat = (await CategoryRepository(session).list_for_user(user.id, CategoryType.income))[0]

    await service.add_income_or_expense(
        user_id=user.id, type_=TransactionType.income, amount=850_000,
        category=income_cat, payment_method=PaymentMethod.cash, transaction_date=dt(),
    )
    await service.add_income_or_expense(
        user_id=user.id, type_=TransactionType.income, amount=4_250_000,
        category=income_cat, payment_method=PaymentMethod.card, transaction_date=dt(),
    )

    balance = await BalanceService(TransactionRepository(session)).get_balance(user.id)
    assert balance.cash == 850_000
    assert balance.card == 4_250_000
    assert balance.total == 5_100_000


async def test_transfer_cash_to_card(session: AsyncSession, user: User) -> None:
    service = await _setup(session, user)
    income_cat = (await CategoryRepository(session).list_for_user(user.id, CategoryType.income))[0]
    await service.add_income_or_expense(
        user_id=user.id, type_=TransactionType.income, amount=1_000_000,
        category=income_cat, payment_method=PaymentMethod.cash, transaction_date=dt(),
    )

    balance_before = await BalanceService(TransactionRepository(session)).get_balance(user.id)
    await service.add_transfer(
        user_id=user.id, amount=500_000,
        from_method=PaymentMethod.cash, to_method=PaymentMethod.card, transaction_date=dt(),
    )
    balance_after = await BalanceService(TransactionRepository(session)).get_balance(user.id)

    assert balance_after.cash == balance_before.cash - 500_000
    assert balance_after.card == balance_before.card + 500_000
    assert balance_after.total == balance_before.total  # transfers never change the total


async def test_transfer_card_to_cash(session: AsyncSession, user: User) -> None:
    service = await _setup(session, user)
    income_cat = (await CategoryRepository(session).list_for_user(user.id, CategoryType.income))[0]
    await service.add_income_or_expense(
        user_id=user.id, type_=TransactionType.income, amount=1_000_000,
        category=income_cat, payment_method=PaymentMethod.card, transaction_date=dt(),
    )

    balance_before = await BalanceService(TransactionRepository(session)).get_balance(user.id)
    await service.add_transfer(
        user_id=user.id, amount=300_000,
        from_method=PaymentMethod.card, to_method=PaymentMethod.cash, transaction_date=dt(),
    )
    balance_after = await BalanceService(TransactionRepository(session)).get_balance(user.id)

    assert balance_after.card == balance_before.card - 300_000
    assert balance_after.cash == balance_before.cash + 300_000
    assert balance_after.total == balance_before.total
