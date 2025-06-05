from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from developer.database.models import Language, LanguageTranslation
from typing import Optional


class LanguageService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session