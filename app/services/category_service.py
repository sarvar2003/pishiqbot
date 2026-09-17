from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Category, CategoryType
from app.database.repositories.category_repo import CategoryRepository
from app.utils.exceptions import InvalidAmountError, NotFoundError

MAX_NAME_LENGTH = 64


class CategoryService:
    def __init__(self, session: AsyncSession, category_repo: CategoryRepository):
        self.session = session
        self.category_repo = category_repo

    def _validate_name(self, name: str) -> str:
        name = name.strip()
        if not name:
            raise InvalidAmountError("❌ Kategoriya nomi bo'sh bo'lishi mumkin emas.")
        if len(name) > MAX_NAME_LENGTH:
            raise InvalidAmountError(f"❌ Kategoriya nomi juda uzun (max {MAX_NAME_LENGTH} belgi).")
        return name

    async def list_categories(self, user_id: int, type_: CategoryType) -> list[Category]:
        return await self.category_repo.list_for_user(user_id, type_)

    async def create_category(
        self, user_id: int, type_: CategoryType, name: str, icon: str = "📦"
    ) -> Category:
        name = self._validate_name(name)
        existing = await self.category_repo.get_by_name(user_id, type_, name)
        if existing is not None and existing.is_active:
            raise InvalidAmountError("❌ Bu nomdagi kategoriya allaqachon mavjud.")
        category = await self.category_repo.create(user_id, type_, name, icon)
        await self.session.commit()
        return category

    async def rename_category(self, category_id: int, user_id: int, new_name: str) -> Category:
        new_name = self._validate_name(new_name)
        category = await self.category_repo.get_by_id(category_id, user_id)
        if category is None:
            raise NotFoundError("❌ Kategoriya topilmadi.")
        existing = await self.category_repo.get_by_name(user_id, category.type, new_name)
        if existing is not None and existing.is_active and existing.id != category.id:
            raise InvalidAmountError("❌ Bu nomdagi kategoriya allaqachon mavjud.")
        await self.category_repo.rename(category, new_name)
        await self.session.commit()
        return category

    async def delete_category(self, category_id: int, user_id: int) -> bool:
        """Deletes the category. Returns True if hard-deleted, False if soft-deleted (in use)."""
        category = await self.category_repo.get_by_id(category_id, user_id)
        if category is None:
            raise NotFoundError("❌ Kategoriya topilmadi.")
        in_use = await self.category_repo.has_transactions(category_id)
        if in_use:
            await self.category_repo.deactivate(category)
            await self.session.commit()
            return False
        await self.category_repo.delete(category)
        await self.session.commit()
        return True
