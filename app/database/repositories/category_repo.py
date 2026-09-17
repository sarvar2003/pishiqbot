from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Category, CategoryType, Transaction


class CategoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_user(
        self, user_id: int, type_: CategoryType, active_only: bool = True
    ) -> list[Category]:
        stmt = select(Category).where(Category.user_id == user_id, Category.type == type_)
        if active_only:
            stmt = stmt.where(Category.is_active.is_(True))
        stmt = stmt.order_by(Category.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, category_id: int, user_id: int) -> Category | None:
        result = await self.session.execute(
            select(Category).where(Category.id == category_id, Category.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, user_id: int, type_: CategoryType, name: str) -> Category | None:
        result = await self.session.execute(
            select(Category).where(
                Category.user_id == user_id,
                Category.type == type_,
                Category.name == name,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: int, type_: CategoryType, name: str, icon: str) -> Category:
        category = Category(user_id=user_id, type=type_, name=name, icon=icon)
        self.session.add(category)
        await self.session.flush()
        return category

    async def rename(self, category: Category, new_name: str) -> Category:
        category.name = new_name
        await self.session.flush()
        return category

    async def has_transactions(self, category_id: int) -> bool:
        result = await self.session.execute(
            select(Transaction.id).where(Transaction.category_id == category_id).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def deactivate(self, category: Category) -> None:
        category.is_active = False
        await self.session.flush()

    async def delete(self, category: Category) -> None:
        await self.session.delete(category)
        await self.session.flush()

    async def seed_defaults(self, user_id: int) -> None:
        defaults_expense = [
            ("🍔", "Oziq-ovqat"),
            ("🚕", "Transport"),
            ("🏠", "Uy"),
            ("🛍", "Xaridlar"),
            ("🎮", "Ko'ngilochar"),
            ("📚", "Ta'lim"),
            ("💻", "Texnologiya"),
            ("💊", "Sog'liq"),
            ("👕", "Kiyim"),
            ("✈️", "Sayohat"),
            ("📱", "Aloqa"),
            ("💳", "Obunalar"),
            ("🎁", "Sovg'a"),
            ("📦", "Boshqa"),
        ]
        defaults_income = [
            ("💼", "Maosh"),
            ("💻", "Freelance"),
            ("🎁", "Sovg'a"),
            ("💰", "Investitsiya"),
            ("🔄", "Qaytarilgan pul"),
            ("📦", "Boshqa"),
        ]
        for icon, name in defaults_expense:
            self.session.add(Category(user_id=user_id, type=CategoryType.expense, name=name, icon=icon))
        for icon, name in defaults_income:
            self.session.add(Category(user_id=user_id, type=CategoryType.income, name=name, icon=icon))
        await self.session.flush()
