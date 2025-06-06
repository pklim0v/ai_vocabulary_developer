from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from developer.database.models import Language, LanguageTranslation
from typing import Optional, List


class LanguageService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ========== BASIC CRUD OPERATIONS ==========

    async def get_language_by_id(self, language_id: int) -> Optional[Language]:
        """
        Receive language by id with translations loaded
        """
        result = await self.session.execute(
            select(Language)
            .options(selectinload(Language.translations).selectinload(LanguageTranslation.locale))
            .where(Language.id == language_id)
        )
        return result.scalars().first()

    async def get_language_by_code(self, code: str) -> Optional[Language]:
        """
        Receive language by code with translations loaded
        :param self:
        :param code:
        :return:
        """
        result = await self.session.execute(
            select(Language)
            .options(selectinload(Language.translations).selectinload(LanguageTranslation.locale))
            .where(Language.code == code)
        )
        return result.scalars().first()

    async def get_all_languages(self, interface_only: bool = False) -> List[Language]:
        """
        Receive all languages with translations loaded
        """
        query = select(Language).options(
            selectinload(Language.translations).selectinload(LanguageTranslation.locale)
        )

        if interface_only:
            query = query.where(Language.is_interface_language == True)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_interface_languages(self) -> List[Language]:
        """
        Receive all interface languages
        :param self:
        :return:
        """
        return await self.get_all_languages(interface_only=True)