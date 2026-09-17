from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.database.models import Category, Transaction, TransactionType

CB_PAGE_PREFIX = "txpage:"
CB_OPEN_PREFIX = "txopen:"
CB_FILTER = "txfilter"


def history_keyboard(
    transactions: list[Transaction], page: int, total_pages: int
) -> InlineKeyboardMarkup:
    rows = []
    for t in transactions:
        icon = "➕" if t.type == TransactionType.income else ("➖" if t.type == TransactionType.expense else "🔄")
        label = f"{icon} {t.transaction_date.strftime('%d.%m')} · {t.amount:,}".replace(",", " ")
        rows.append([InlineKeyboardButton(text=label, callback_data=f"{CB_OPEN_PREFIX}{t.id}")])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"{CB_PAGE_PREFIX}{page - 1}"))
    if total_pages > 0:
        nav_row.append(
            InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop")
        )
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"{CB_PAGE_PREFIX}{page + 1}"))
    if nav_row:
        rows.append(nav_row)

    rows.append([InlineKeyboardButton(text="🔍 Filtr", callback_data=CB_FILTER)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def transaction_detail_keyboard(transaction_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"txedit:{transaction_id}"),
                InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"txdel:{transaction_id}"),
            ],
            [InlineKeyboardButton(text="⬅️ Ro'yxatga qaytish", callback_data=f"{CB_PAGE_PREFIX}0")],
        ]
    )


def filter_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Kirim", callback_data="txf_type:income"),
                InlineKeyboardButton(text="➖ Chiqim", callback_data="txf_type:expense"),
            ],
            [InlineKeyboardButton(text="🔄 O'tkazmalar", callback_data="txf_type:transfer")],
            [
                InlineKeyboardButton(text="💵 Naqd", callback_data="txf_pay:cash"),
                InlineKeyboardButton(text="💳 Karta", callback_data="txf_pay:card"),
            ],
            [InlineKeyboardButton(text="📂 Kategoriya bo'yicha", callback_data="txf_cat_menu")],
            [InlineKeyboardButton(text="♻️ Filtrni tozalash", callback_data="txf_clear")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"{CB_PAGE_PREFIX}0")],
        ]
    )


def filter_category_keyboard(categories: list[Category], columns: int = 2) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=c.display_name, callback_data=f"txf_cat:{c.id}") for c in categories
    ]
    rows = [buttons[i : i + columns] for i in range(0, len(buttons), columns)]
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=CB_FILTER)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def edit_field_keyboard(transaction_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💰 Summa", callback_data=f"txeditfield:{transaction_id}:amount")],
            [InlineKeyboardButton(text="📂 Kategoriya", callback_data=f"txeditfield:{transaction_id}:category")],
            [InlineKeyboardButton(text="💳 To'lov usuli", callback_data=f"txeditfield:{transaction_id}:payment")],
            [InlineKeyboardButton(text="📝 Izoh", callback_data=f"txeditfield:{transaction_id}:note")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"txopen:{transaction_id}")],
        ]
    )


def delete_confirmation_keyboard(transaction_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"txdelyes:{transaction_id}"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data=f"txopen:{transaction_id}"),
            ]
        ]
    )
