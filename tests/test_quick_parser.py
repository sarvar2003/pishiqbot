from __future__ import annotations

from app.database.models import Category, CategoryType, PaymentMethod, TransactionType
from app.services.quick_parser import parse_quick_entry


def _cat(id_: int, name: str, type_: CategoryType) -> Category:
    return Category(id=id_, user_id=1, name=name, type=type_, icon="📦", is_active=True)


CATEGORIES = [
    _cat(1, "Oziq-ovqat", CategoryType.expense),
    _cat(2, "Transport", CategoryType.expense),
    _cat(3, "Freelance", CategoryType.income),
    _cat(4, "Qaytarilgan pul", CategoryType.income),
]


def test_expense_quick_entry_fully_resolved() -> None:
    result = parse_quick_entry("- 150000 oziq-ovqat karta", CATEGORIES)

    assert result is not None
    assert result.type == TransactionType.expense
    assert result.amount == 150000
    assert result.matched_category.name == "Oziq-ovqat"
    assert result.payment_method == PaymentMethod.card
    assert result.is_fully_resolved


def test_income_quick_entry_fully_resolved() -> None:
    result = parse_quick_entry("+ 500000 freelance karta", CATEGORIES)

    assert result is not None
    assert result.type == TransactionType.income
    assert result.amount == 500000
    assert result.matched_category.name == "Freelance"
    assert result.payment_method == PaymentMethod.card


def test_quick_entry_with_note() -> None:
    result = parse_quick_entry("- 150000 oziq-ovqat karta tushlik uchun", CATEGORIES)

    assert result.note == "tushlik uchun"


def test_quick_entry_multi_word_category() -> None:
    result = parse_quick_entry("+ 100000 qaytarilgan pul karta", CATEGORIES)

    assert result.matched_category.name == "Qaytarilgan pul"


def test_quick_entry_missing_payment_method() -> None:
    result = parse_quick_entry("- 150000 oziq-ovqat", CATEGORIES)

    assert result is not None
    assert result.matched_category.name == "Oziq-ovqat"
    assert result.payment_method is None
    assert not result.is_fully_resolved


def test_quick_entry_unknown_category_does_not_guess() -> None:
    result = parse_quick_entry("- 150000 notavalidcategory karta", CATEGORIES)

    assert result is not None
    assert result.matched_category is None
    assert not result.is_fully_resolved


def test_quick_entry_invalid_amount() -> None:
    result = parse_quick_entry("- 0 oziq-ovqat karta", CATEGORIES)

    assert result is not None
    assert result.amount is None
    assert result.amount_error is not None


def test_not_a_quick_entry_returns_none() -> None:
    assert parse_quick_entry("Salom, qandaysiz?", CATEGORIES) is None
    assert parse_quick_entry("/start", CATEGORIES) is None
