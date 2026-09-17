from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = logging.getLogger(__name__)

UNAUTHORIZED_MESSAGE = "⛔️ Kechirasiz, bu bot faqat egasi uchun mo'ljallangan."


class AuthMiddleware(BaseMiddleware):
    """Rejects any Message/CallbackQuery from a Telegram user other than the configured owner."""

    def __init__(self, allowed_user_id: int):
        self.allowed_user_id = allowed_user_id
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)

        user = event.from_user
        if user is None or user.id != self.allowed_user_id:
            logger.warning("Rejected update from unauthorized telegram_id=%s", user.id if user else None)
            if isinstance(event, Message):
                await event.answer(UNAUTHORIZED_MESSAGE)
            else:
                await event.answer(UNAUTHORIZED_MESSAGE, show_alert=True)
            return None

        return await handler(event, data)
