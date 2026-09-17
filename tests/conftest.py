from __future__ import annotations

import datetime
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database.models import Base, User
from app.database.repositories.category_repo import CategoryRepository
from app.database.repositories.user_repo import UserRepository

TASHKENT = ZoneInfo("Asia/Tashkent")


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as s:
        yield s

    await engine.dispose()


@pytest_asyncio.fixture
async def user(session: AsyncSession) -> User:
    user_repo = UserRepository(session)
    db_user = await user_repo.create(telegram_id=123456789, username="tester", first_name="Test")
    await CategoryRepository(session).seed_defaults(db_user.id)
    await session.commit()
    return db_user


def dt(days_ago: int = 0, hour: int = 12) -> datetime.datetime:
    now = datetime.datetime.now(TASHKENT)
    return (now - datetime.timedelta(days=days_ago)).replace(hour=hour, minute=0, second=0, microsecond=0)
