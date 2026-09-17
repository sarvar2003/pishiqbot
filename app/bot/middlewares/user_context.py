from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.category_repo import CategoryRepository
from app.database.repositories.user_repo import UserRepository


class UserContextMiddleware(BaseMiddleware):
    """Ensures a User row exists for the current Telegram user and injects it as `db_user`."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, (Message, CallbackQuery)) or event.from_user is None:
            return await handler(event, data)

        session: AsyncSession = data["session"]
        user_repo = UserRepository(session)
        db_user, created = await user_repo.get_or_create(
            telegram_id=event.from_user.id,
            username=event.from_user.username,
            first_name=event.from_user.first_name,
        )
        if created:
            await CategoryRepository(session).seed_defaults(db_user.id)
            await session.commit()

        data["db_user"] = db_user
        return await handler(event, data)
