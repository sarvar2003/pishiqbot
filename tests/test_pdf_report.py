from __future__ import annotations

import datetime

from app.database.models import Category, CategoryType
from app.services.pdf_report_service import build_report_pdf
from app.services.report_service import CategoryBreakdownItem, PeriodSummary


def _category(name: str) -> Category:
    return Category(id=1, user_id=1, name=name, type=CategoryType.expense, icon="📦", is_active=True)


def test_build_report_pdf_returns_valid_pdf_bytes() -> None:
    summary = PeriodSummary(label="Bu oy", income=8_500_000, expense=3_200_000)
    breakdown = [
        CategoryBreakdownItem(category=_category("Oziq-ovqat"), amount=850_000, percent=61.8),
        CategoryBreakdownItem(category=_category("Transport"), amount=525_000, percent=38.2),
    ]

    pdf_bytes = build_report_pdf("Bu oy", summary, breakdown, datetime.datetime(2026, 9, 18, 12, 0))

    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 0


def test_build_report_pdf_handles_empty_breakdown() -> None:
    summary = PeriodSummary(label="Bugun", income=0, expense=0)

    pdf_bytes = build_report_pdf("Bugun", summary, [], datetime.datetime(2026, 9, 18, 12, 0))

    assert pdf_bytes.startswith(b"%PDF")
