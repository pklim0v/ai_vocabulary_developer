from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from developer.database.models import UserAgreement
from typing import Optional

class UserAgreementService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active_agreement(self, locale: str) -> Optional[UserAgreement]:
        result = await self.session.execute(
            select(UserAgreement).filter_by(language_code=locale, is_active=True)
        )

        # if there is no active agreement for locale, try to get active agreement for 'en' locale
        if not result.scalars().all():
            locale = 'en'
            result = await self.session.execute(
                select(UserAgreement).filter_by(language_code=locale, is_active=True)
            )

        return result.scalars().one_or_none()
