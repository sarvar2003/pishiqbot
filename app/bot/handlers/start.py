from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.bot.keyboards.main_menu import main_menu_keyboard
from app.database.models import User

router = Router(name="start")


@router.message(CommandStart())
async def start_command(message: Message, db_user: User) -> None:
    name = db_user.first_name or "foydalanuvchi"
    await message.answer(
        f"Salom, {name}! 👋\n\n"
        "Men shaxsiy kirim-chiqim hisobchi botman.\n"
        "Quyidagi menyudan kerakli amalni tanlang:",
        reply_markup=main_menu_keyboard(),
    )
