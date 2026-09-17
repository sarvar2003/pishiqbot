from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import CategoryType, PaymentMethod, TransactionType, User
from app.database.repositories.category_repo import CategoryRepository
from app.database.repositories.transaction_repo import TransactionRepository
from app.services.transaction_service import TransactionService, validate_amount
from app.utils.exceptions import InvalidAmountError, NotFoundError
from tests.conftest import dt


async def _service(session: AsyncSession) -> TransactionService:
    return TransactionService(session, TransactionRepository(session), CategoryRepository(session))


async def _category(session: AsyncSession, user: User, type_: CategoryType):
    categories = await CategoryRepository(session).list_for_user(user.id, type_)
    return categories[0]


async def test_add_income(session: AsyncSession, user: User) -> None:
    service = await _service(session)
    category = await _category(session, user, CategoryType.income)

    tx = await service.add_income_or_expense(
        user_id=user.id,
        type_=TransactionType.income,
        amount=500_000,
        category=category,
        payment_method=PaymentMethod.card,
        transaction_date=dt(),
    )

    assert tx.id is not None
    assert tx.type == TransactionType.income
    assert tx.amount == 500_000


async def test_add_expense(session: AsyncSession, user: User) -> None:
    service = await _service(session)
    category = await _category(session, user, CategoryType.expense)

    tx = await service.add_income_or_expense(
        user_id=user.id,
        type_=TransactionType.expense,
        amount=150_000,
        category=category,
        payment_method=PaymentMethod.cash,
        transaction_date=dt(),
    )

    assert tx.type == TransactionType.expense
    assert tx.amount == 150_000


async def test_delete_transaction(session: AsyncSession, user: User) -> None:
    service = await _service(session)
    category = await _category(session, user, CategoryType.expense)
    tx = await service.add_income_or_expense(
        user_id=user.id,
        type_=TransactionType.expense,
        amount=100_000,
        category=category,
        payment_method=PaymentMethod.cash,
        transaction_date=dt(),
    )

    await service.delete_transaction(tx.id, user.id)

    with pytest.raises(NotFoundError):
        await service.get_transaction(tx.id, user.id)


async def test_edit_transaction_amount_and_payment(session: AsyncSession, user: User) -> None:
    service = await _service(session)
    category = await _category(session, user, CategoryType.expense)
    tx = await service.add_income_or_expense(
        user_id=user.id,
        type_=TransactionType.expense,
        amount=100_000,
        category=category,
        payment_method=PaymentMethod.cash,
        transaction_date=dt(),
    )

    updated = await service.update_transaction(tx.id, user.id, amount=250_000, payment_method=PaymentMethod.card)

    assert updated.amount == 250_000
    assert updated.payment_method == PaymentMethod.card


async def test_edit_transaction_not_found(session: AsyncSession, user: User) -> None:
    service = await _service(session)
    with pytest.raises(NotFoundError):
        await service.update_transaction(999_999, user.id, amount=100)


@pytest.mark.parametrize("raw", ["abc", "", "  ", "12.5.6", "1o0000"])
async def test_validate_amount_invalid(raw: str) -> None:
    with pytest.raises(InvalidAmountError):
        validate_amount(raw)


async def test_validate_amount_zero() -> None:
    with pytest.raises(InvalidAmountError):
        validate_amount("0")


async def test_validate_amount_negative() -> None:
    with pytest.raises(InvalidAmountError):
        validate_amount("-5000")


async def test_validate_amount_valid_with_spaces() -> None:
    assert validate_amount("150 000") == 150_000


async def test_add_transaction_rejects_non_positive_amount(session: AsyncSession, user: User) -> None:
    service = await _service(session)
    category = await _category(session, user, CategoryType.expense)
    with pytest.raises(InvalidAmountError):
        await service.add_income_or_expense(
            user_id=user.id,
            type_=TransactionType.expense,
            amount=0,
            category=category,
            payment_method=PaymentMethod.cash,
            transaction_date=dt(),
        )
