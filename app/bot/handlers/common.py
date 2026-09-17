from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ErrorEvent, Message

from app.bot.keyboards.main_menu import main_menu_keyboard
from app.utils.exceptions import AppError

logger = logging.getLogger(__name__)

router = Router(name="common")


@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    await state.clear()
    if current_state is None:
        await message.answer("Bekor qilish uchun hech narsa yo'q.", reply_markup=main_menu_keyboard())
        return
    await message.answer("❌ Amal bekor qilindi.", reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery) -> None:
    await callback.answer()


@router.error()
async def error_handler(event: ErrorEvent) -> None:
    exc = event.exception
    if isinstance(exc, AppError):
        text = exc.user_message
        logger.info("Handled AppError: %s", text)
    else:
        text = "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring."
        logger.exception("Unhandled error while processing update", exc_info=exc)

    update = event.update
    try:
        if update.message is not None:
            await update.message.answer(text)
        elif update.callback_query is not None:
            await update.callback_query.answer(text, show_alert=True)
    except Exception:  # noqa: BLE001 - error handler must never itself raise
        logger.exception("Failed to notify user about error")
