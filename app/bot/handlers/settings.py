from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers.shared import cancel_flow, get_category_service
from app.bot.keyboards.categories import (
    categories_management_keyboard,
    category_edit_keyboard,
    category_type_choice_keyboard,
)
from app.bot.keyboards.common import CB_BACK, CB_CANCEL, cancel_only_keyboard, yes_no_keyboard
from app.bot.keyboards.main_menu import BTN_SETTINGS
from app.bot.keyboards.settings import CB_SETTINGS_CATEGORIES, settings_menu_keyboard
from app.bot.states.transaction_states import CategoryStates
from app.database.models import CategoryType, User
from app.database.repositories.category_repo import CategoryRepository
from app.utils.exceptions import AppError

router = Router(name="settings")


def _list_title(type_: CategoryType) -> str:
    return "➕ Kirim kategoriyalari" if type_ == CategoryType.income else "➖ Chiqim kategoriyalari"


async def _show_list(target, session: AsyncSession, db_user: User, type_: CategoryType, as_new: bool = False) -> None:
    categories = await CategoryRepository(session).list_for_user(db_user.id, type_)
    text = _list_title(type_)
    keyboard = categories_management_keyboard(categories)
    if as_new:
        await target.answer(text, reply_markup=keyboard)
    else:
        await target.message.edit_text(text, reply_markup=keyboard)


@router.message(F.text == BTN_SETTINGS)
async def show_settings(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("⚙️ Sozlamalar", reply_markup=settings_menu_keyboard())


@router.callback_query(F.data == CB_SETTINGS_CATEGORIES)
async def settings_categories(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CategoryStates.choosing_type)
    await callback.message.edit_text(
        "🗂 Qaysi kategoriyalar turini boshqarmoqchisiz?", reply_markup=category_type_choice_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == CB_BACK, StateFilter(CategoryStates.choosing_type))
async def back_to_settings_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("⚙️ Sozlamalar", reply_markup=settings_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("cattype:"), StateFilter(CategoryStates.choosing_type))
async def choose_category_type(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    type_ = CategoryType(callback.data.removeprefix("cattype:"))
    await state.update_data(manage_type=type_.value)
    await state.set_state(CategoryStates.browsing_list)
    await _show_list(callback, session, db_user, type_)
    await callback.answer()


@router.callback_query(F.data == CB_BACK, StateFilter(CategoryStates.browsing_list))
async def back_to_type_choice(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CategoryStates.choosing_type)
    await callback.message.edit_text(
        "🗂 Qaysi kategoriyalar turini boshqarmoqchisiz?", reply_markup=category_type_choice_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "catmanage:new", StateFilter(CategoryStates.browsing_list))
async def start_create_category(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CategoryStates.waiting_name_for_create)
    await callback.message.edit_text("Yangi kategoriya nomini kiriting:", reply_markup=cancel_only_keyboard())
    await callback.answer()


@router.callback_query(
    F.data.startswith("catmanage:"),
    StateFilter(CategoryStates.browsing_list, CategoryStates.viewing_category),
)
async def open_category(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    category_id = int(callback.data.removeprefix("catmanage:"))
    category = await CategoryRepository(session).get_by_id(category_id, db_user.id)
    if category is None:
        await callback.answer("❌ Kategoriya topilmadi.", show_alert=True)
        return
    await state.update_data(viewing_category_id=category.id)
    await state.set_state(CategoryStates.viewing_category)
    await callback.message.edit_text(
        f"Kategoriya: {category.display_name}\n\nNima qilmoqchisiz?",
        reply_markup=category_edit_keyboard(category.id),
    )
    await callback.answer()


@router.callback_query(F.data == CB_BACK, StateFilter(CategoryStates.viewing_category))
async def back_to_list(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    data = await state.get_data()
    type_ = CategoryType(data["manage_type"])
    await state.set_state(CategoryStates.browsing_list)
    await _show_list(callback, session, db_user, type_)
    await callback.answer()


@router.callback_query(F.data.startswith("catrename:"), StateFilter(CategoryStates.viewing_category))
async def start_rename(callback: CallbackQuery, state: FSMContext) -> None:
    category_id = int(callback.data.removeprefix("catrename:"))
    await state.update_data(rename_category_id=category_id)
    await state.set_state(CategoryStates.waiting_name_for_rename)
    await callback.message.edit_text("Yangi nomni kiriting:", reply_markup=cancel_only_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("catdelete:"), StateFilter(CategoryStates.viewing_category))
async def ask_delete_category(callback: CallbackQuery) -> None:
    category_id = int(callback.data.removeprefix("catdelete:"))
    await callback.message.edit_text(
        "🗑 Haqiqatan ham o'chirmoqchimisiz?",
        reply_markup=yes_no_keyboard(f"catdelyes:{category_id}", f"catmanage:{category_id}"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("catdelyes:"), StateFilter(CategoryStates.viewing_category))
async def confirm_delete_category(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    category_id = int(callback.data.removeprefix("catdelyes:"))
    service = get_category_service(session)
    hard_deleted = await service.delete_category(category_id, db_user.id)
    text = "✅ Kategoriya o'chirildi." if hard_deleted else "ℹ️ Kategoriya tranzaksiyalarda ishlatilgani uchun yashirildi."
    await callback.answer(text, show_alert=True)

    data = await state.get_data()
    type_ = CategoryType(data["manage_type"])
    await state.set_state(CategoryStates.browsing_list)
    await _show_list(callback, session, db_user, type_)


@router.message(CategoryStates.waiting_name_for_create)
async def create_category(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    data = await state.get_data()
    type_ = CategoryType(data["manage_type"])
    icon = "💰" if type_ == CategoryType.income else "📦"
    service = get_category_service(session)
    try:
        await service.create_category(db_user.id, type_, message.text or "", icon=icon)
    except AppError as exc:
        await message.answer(exc.user_message)
        return

    await state.set_state(CategoryStates.browsing_list)
    await message.answer("✅ Kategoriya qo'shildi!")
    await _show_list(message, session, db_user, type_, as_new=True)


@router.message(CategoryStates.waiting_name_for_rename)
async def rename_category(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    data = await state.get_data()
    category_id = data["rename_category_id"]
    service = get_category_service(session)
    try:
        await service.rename_category(category_id, db_user.id, message.text or "")
    except AppError as exc:
        await message.answer(exc.user_message)
        return

    type_ = CategoryType(data["manage_type"])
    await state.set_state(CategoryStates.browsing_list)
    await message.answer("✅ Nomi o'zgartirildi!")
    await _show_list(message, session, db_user, type_, as_new=True)


@router.callback_query(F.data == CB_CANCEL, StateFilter(CategoryStates))
async def cancel_category_flow(callback: CallbackQuery, state: FSMContext) -> None:
    await cancel_flow(callback, state)
