from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload, joinedload
from developer.database.models import UserAgreement, Language
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class UserAgreementService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active_agreement(self, locale_code: str) -> Optional[UserAgreement]:
        """
        Retrieve the active user agreement for a given locale. If no active agreement exists
        for the requested locale, an attempt is made to fetch the agreement for English ('en')
        locale as a fallback.

        :param locale_code: The code of the locale for which the user agreement
            needs to be fetched.
        :type locale_code: str
        :return: The active UserAgreement object for the requested locale if available,
            otherwise the agreement for the English locale if available, or None if
            no active agreement is found.
        :rtype: Optional[UserAgreement]
        """
        # At first, try to find an active agreement for the requested locale.
        result = await self.session.execute(
            select(UserAgreement)
            .join(Language, UserAgreement.agreement_language_id == Language.id)
            .options(selectinload(UserAgreement.agreement_language))
            .where(
                and_(
                    Language.code == locale_code,
                    UserAgreement.is_active == True
                )
            )
        )

        agreement = result.scalars().first()

        # if not found, try to find an active agreement for English locale.
        if not agreement and locale_code != 'en':
            logger.info(f"No active agreement found for {locale_code}, trying English")
            result = await self.session.execute(
                select(UserAgreement)
                .join(Language, UserAgreement.agreement_language_id == Language.id)
                .options(selectinload(UserAgreement.agreement_language))
                .where(
                    and_(
                        Language.code == 'en',
                        UserAgreement.is_active == True
                    )
                )
            )
            agreement = result.scalars().first()

        return agreement

    async def get_active_agreement_by_language_id(self, language_id: int) -> Optional[UserAgreement]:
        """
        Получить активное соглашение по ID языка

        :param language_id: ID языка
        :return: активное соглашение или None
        """
        result = await self.session.execute(
            select(UserAgreement)
            .options(selectinload(UserAgreement.agreement_language))
            .where(
                and_(
                    UserAgreement.agreement_language_id == language_id,
                    UserAgreement.is_active == True
                )
            )
        )
        return result.scalars().first()

    async def get_all_active_agreements(self) -> List[UserAgreement]:
        """Получить все активные соглашения"""
        result = await self.session.execute(
            select(UserAgreement)
            .options(selectinload(UserAgreement.agreement_language))
            .where(UserAgreement.is_active == True)
            .order_by(UserAgreement.version.desc(), UserAgreement.created_at.desc())
        )
        return result.scalars().all()

    async def get_agreements_by_version(self, version: str) -> List[UserAgreement]:
        """Получить все соглашения определенной версии"""
        result = await self.session.execute(
            select(UserAgreement)
            .options(selectinload(UserAgreement.agreement_language))
            .where(UserAgreement.version == version)
            .order_by(UserAgreement.agreement_language_id)
        )
        return result.scalars().all()

    async def get_latest_agreement_for_language(self, locale_code: str) -> Optional[UserAgreement]:
        """
        Получить последнее соглашение для языка (активное или неактивное)

        :param locale_code: код языка
        :return: последнее соглашение или None
        """
        result = await self.session.execute(
            select(UserAgreement)
            .join(Language, UserAgreement.agreement_language_id == Language.id)
            .options(selectinload(UserAgreement.agreement_language))
            .where(Language.code == locale_code)
            .order_by(UserAgreement.version.desc(), UserAgreement.created_at.desc())
        )
        return result.scalars().first()

    async def create_agreement(
            self,
            version: str,
            language_code: str,
            url: str,
            is_active: bool = False
    ) -> Optional[UserAgreement]:
        """
        Создать новое пользовательское соглашение

        :param version: версия соглашения
        :param language_code: код языка
        :param url: URL соглашения
        :param is_active: активно ли соглашение
        :return: созданное соглашение или None
        """
        # Находим язык по коду
        language_result = await self.session.execute(
            select(Language).where(Language.code == language_code)
        )
        language = language_result.scalars().first()

        if not language:
            logger.error(f"Language with code '{language_code}' not found")
            return None

        # Проверяем, что соглашение такой версии для этого языка не существует
        existing = await self.session.execute(
            select(UserAgreement).where(
                and_(
                    UserAgreement.version == version,
                    UserAgreement.agreement_language_id == language.id
                )
            )
        )

        if existing.scalars().first():
            logger.warning(f"Agreement version {version} for language {language_code} already exists")
            return None

        agreement = UserAgreement(
            version=version,
            agreement_language_id=language.id,
            url=url,
            is_active=is_active
        )

        self.session.add(agreement)
        await self.session.commit()
        await self.session.refresh(agreement)

        logger.info(f"Created agreement {version} for language {language_code}")
        return agreement

    async def activate_agreement(self, agreement_id: int, admin_user_id: int) -> bool:
        """
        Активировать соглашение (и деактивировать другие для того же языка)

        :param agreement_id: ID соглашения
        :param admin_user_id: ID администратора
        :return: успешно ли активировано
        """
        # Получаем соглашение
        agreement_result = await self.session.execute(
            select(UserAgreement)
            .options(selectinload(UserAgreement.agreement_language))
            .where(UserAgreement.id == agreement_id)
        )
        agreement = agreement_result.scalars().first()

        if not agreement:
            return False

        # Деактивируем все другие соглашения для этого языка
        await self.session.execute(
            update(UserAgreement)
            .where(
                and_(
                    UserAgreement.agreement_language_id == agreement.agreement_language_id,
                    UserAgreement.id != agreement_id
                )
            )
            .values(is_active=False)
        )

        # Активируем выбранное соглашение
        agreement.is_active = True
        agreement.activated_at = datetime.now()
        agreement.activated_by_id = admin_user_id

        await self.session.commit()
        logger.info(f"Activated agreement {agreement.version} for language {agreement.agreement_language.code}")
        return True

    async def deactivate_agreement(self, agreement_id: int, admin_user_id: int) -> bool:
        """
        Деактивировать соглашение

        :param agreement_id: ID соглашения
        :param admin_user_id: ID администратора
        :return: успешно ли деактивировано
        """
        agreement_result = await self.session.execute(
            select(UserAgreement).where(UserAgreement.id == agreement_id)
        )
        agreement = agreement_result.scalars().first()

        if not agreement:
            return False

        agreement.is_active = False
        agreement.deactivated_at = datetime.now()
        agreement.deactivated_by_id = admin_user_id

        await self.session.commit()
        logger.info(f"Deactivated agreement {agreement.version}")
        return True

    async def get_user_agreement_for_locale(self, user_locale_code: str) -> Optional[UserAgreement]:
        """
        Получить подходящее соглашение для пользователя с учетом его локали

        :param user_locale_code: код языка пользователя
        :return: подходящее соглашение
        """
        # Сначала пытаемся найти на языке пользователя
        agreement = await self.get_active_agreement(user_locale_code)

        # Если не найдено, берем английское
        if not agreement:
            agreement = await self.get_active_agreement('en')

        # Если и английского нет, берем любое активное
        if not agreement:
            agreements = await self.get_all_active_agreements()
            agreement = agreements[0] if agreements else None

            if agreement:
                logger.warning(
                    f"No agreement found for {user_locale_code} or 'en', using {agreement.agreement_language.code}")

        return agreement

    async def check_agreement_exists_for_language(self, language_code: str, version: str = None) -> bool:
        """
        Проверить, существует ли соглашение для языка

        :param language_code: код языка
        :param version: версия (опционально)
        :return: True если существует
        """
        query = (
            select(UserAgreement)
            .join(Language, UserAgreement.agreement_language_id == Language.id)
            .where(Language.code == language_code)
        )

        if version:
            query = query.where(UserAgreement.version == version)

        result = await self.session.execute(query)
        return result.scalars().first() is not None

    async def get_agreements_summary(self) -> List[dict]:
        """
        Получить сводку по всем соглашениям

        :return: список словарей с информацией о соглашениях
        """
        result = await self.session.execute(
            select(UserAgreement, Language.code, Language.flag_code)
            .join(Language, UserAgreement.agreement_language_id == Language.id)
            .order_by(UserAgreement.version.desc(), Language.code)
        )

        agreements_data = []
        for agreement, lang_code, flag_code in result:
            agreements_data.append({
                'id': agreement.id,
                'version': agreement.version,
                'language_code': lang_code,
                'flag_code': flag_code,
                'url': agreement.url,
                'is_active': agreement.is_active,
                'created_at': agreement.created_at,
                'activated_at': agreement.activated_at
            })

        return agreements_data