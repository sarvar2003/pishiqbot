from __future__ import annotations

import datetime

from fpdf import FPDF

from app.services.report_service import CategoryBreakdownItem, PeriodSummary
from app.utils.formatting import format_amount, format_datetime, format_signed_amount

# fpdf2's core fonts (Helvetica/Times/Courier) only support Latin-1, not emoji.
# Category icons are dropped here on purpose - category.name (plain text) is used
# instead of category.display_name. Uzbek Latin text itself is plain ASCII plus a
# straight apostrophe, so it renders fine without embedding a custom Unicode font.


def build_report_pdf(
    label: str,
    summary: PeriodSummary,
    breakdown: list[CategoryBreakdownItem],
    generated_at: datetime.datetime,
) -> bytes:
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "Hisobot", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Davr: {label}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Yaratilgan: {format_datetime(generated_at)}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Umumiy ko'rsatkichlar", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Kirim: {format_amount(summary.income)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Chiqim: {format_amount(summary.expense)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Sof o'zgarish: {format_signed_amount(summary.net)}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Chiqimlar (kategoriya bo'yicha)", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    if not breakdown:
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, "Bu davrda chiqimlar yo'q.", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(90, 8, "Kategoriya", border=1, fill=True)
        pdf.cell(50, 8, "Summa", border=1, fill=True, align="R")
        pdf.cell(30, 8, "Ulush", border=1, fill=True, align="R", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 11)
        for item in breakdown:
            pdf.cell(90, 8, item.category.name, border=1)
            pdf.cell(50, 8, format_amount(item.amount), border=1, align="R")
            pdf.cell(30, 8, f"{item.percent:.0f}%", border=1, align="R", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
