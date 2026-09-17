from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, Message, User as TgUser

from app.bot.middlewares.auth import AuthMiddleware

ALLOWED_ID = 111111


def _fake_message(user_id: int) -> Message:
    message = MagicMock(spec=Message)
    message.from_user = TgUser(id=user_id, is_bot=False, first_name="Test")
    message.answer = AsyncMock()
    return message


def _fake_callback(user_id: int) -> CallbackQuery:
    callback = MagicMock(spec=CallbackQuery)
    callback.from_user = TgUser(id=user_id, is_bot=False, first_name="Test")
    callback.answer = AsyncMock()
    return callback


async def test_authorized_user_is_allowed() -> None:
    middleware = AuthMiddleware(ALLOWED_ID)
    handler = AsyncMock(return_value="handled")
    message = _fake_message(ALLOWED_ID)

    result = await middleware(handler, message, {})

    assert result == "handled"
    handler.assert_awaited_once()


async def test_unauthorized_message_is_rejected() -> None:
    middleware = AuthMiddleware(ALLOWED_ID)
    handler = AsyncMock(return_value="handled")
    message = _fake_message(999999)

    result = await middleware(handler, message, {})

    assert result is None
    handler.assert_not_awaited()
    message.answer.assert_awaited_once()


async def test_unauthorized_callback_is_rejected() -> None:
    middleware = AuthMiddleware(ALLOWED_ID)
    handler = AsyncMock(return_value="handled")
    callback = _fake_callback(999999)

    result = await middleware(handler, callback, {})

    assert result is None
    handler.assert_not_awaited()
    callback.answer.assert_awaited_once()
