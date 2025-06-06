from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload, joinedload
from developer.database.models import PrivacyPolicy, Language
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class PrivacyPolicyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active_policy(self, locale_code: str) -> Optional[PrivacyPolicy]:
        """
        Retrieves the active privacy policy for a specified locale code. If no active policy exists
        for the given locale, attempts to retrieve the active policy in English.

        :param locale_code: Locale code used to look up the privacy policy
        :type locale_code: str
        :return: The active privacy policy for the specified locale or None if no
            active policy exists
        :rtype: Optional[PrivacyPolicy]
        """
        # At first, try to find an active policy for the requested locale.
        result = await self.session.execute(
            select(PrivacyPolicy)
            .join(Language, PrivacyPolicy.policy_language_id == Language.id)
            .options(selectinload(PrivacyPolicy.policy_language))
            .where(
                and_(
                    Language.code == locale_code,
                    PrivacyPolicy.is_active == True
                )
            )
        )

        policy = result.scalars().first()

        # if not found, try to find an active policy for English locale.
        if not policy and locale_code != 'en':
            logger.info(f"No active policy found for {locale_code}, trying English")
            result = await self.session.execute(
                select(PrivacyPolicy)
                .join(Language, PrivacyPolicy.policy_language_id == Language.id)
                .options(selectinload(PrivacyPolicy.policy_language))
                .where(
                    and_(
                        Language.code == 'en',
                        PrivacyPolicy.is_active == True
                    )
                )
            )
            policy = result.scalars().first()

        return policy
