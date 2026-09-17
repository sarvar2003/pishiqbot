from __future__ import annotations

import re
from dataclasses import dataclass

from app.database.models import Category, PaymentMethod, TransactionType

_LEADING_PATTERN = re.compile(r"^\s*([+\-])\s*(\d[\d\s]*)\s+(.+)$", re.DOTALL)
_PAYMENT_KEYWORDS = {
    "naqd": PaymentMethod.cash,
    "karta": PaymentMethod.card,
}


@dataclass(frozen=True)
class QuickEntryResult:
    type: TransactionType
    amount: int | None
    amount_error: str | None
    category_query: str
    matched_category: Category | None
    category_ambiguous: bool
    payment_method: PaymentMethod | None
    note: str | None

    @property
    def is_fully_resolved(self) -> bool:
        return (
            self.amount is not None
            and self.amount_error is None
            and self.matched_category is not None
            and not self.category_ambiguous
            and self.payment_method is not None
        )


def _normalize(text: str) -> str:
    text = text.lower().strip()
    for ch in ("'", "’", "‘", "`"):
        text = text.replace(ch, "")
    text = text.replace("-", " ")
    return " ".join(text.split())


def _match_category(query: str, categories: list[Category]) -> tuple[Category | None, bool]:
    """Returns (matched_category, ambiguous). Both None/False means no match found."""
    if not query:
        return None, False
    normalized_query = _normalize(query)
    exact = [c for c in categories if _normalize(c.name) == normalized_query]
    if len(exact) == 1:
        return exact[0], False
    if len(exact) > 1:
        return None, True

    partial = [
        c
        for c in categories
        if normalized_query in _normalize(c.name) or _normalize(c.name) in normalized_query
    ]
    if len(partial) == 1:
        return partial[0], False
    if len(partial) > 1:
        return None, True
    return None, False


def parse_quick_entry(
    text: str, categories: list[Category]
) -> QuickEntryResult | None:
    """Deterministically parses '- 150000 oziq-ovqat karta [note]' style quick entries.

    Returns None if the text doesn't even look like a quick-entry attempt (no leading +/-
    followed by a number), so the caller can fall back to treating it as a normal message.
    """
    match = _LEADING_PATTERN.match(text)
    if not match:
        return None

    sign, raw_amount, rest = match.groups()
    type_ = TransactionType.income if sign == "+" else TransactionType.expense

    amount: int | None
    amount_error: str | None
    cleaned_amount = raw_amount.replace(" ", "")
    if not cleaned_amount.isdigit():
        amount, amount_error = None, "❌ Summa noto'g'ri."
    else:
        parsed = int(cleaned_amount)
        if parsed == 0:
            amount, amount_error = None, "❌ Summa noldan katta bo'lishi kerak."
        else:
            amount, amount_error = parsed, None

    tokens = rest.split()
    payment_idx = None
    payment_method = None
    for idx, token in enumerate(tokens):
        candidate = _PAYMENT_KEYWORDS.get(token.lower())
        if candidate is not None:
            payment_idx = idx
            payment_method = candidate
            break

    if payment_idx is not None:
        category_tokens = tokens[:payment_idx]
        note_tokens = tokens[payment_idx + 1 :]
    else:
        category_tokens = tokens[:1]
        note_tokens = tokens[1:]

    category_query = " ".join(category_tokens)
    matched_category, ambiguous = _match_category(category_query, categories)
    note = " ".join(note_tokens).strip() or None

    return QuickEntryResult(
        type=type_,
        amount=amount,
        amount_error=amount_error,
        category_query=category_query,
        matched_category=matched_category,
        category_ambiguous=ambiguous,
        payment_method=payment_method,
        note=note,
    )
