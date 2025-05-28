from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from developer.database.models import User
from typing import Optional


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).filter_by(telegram_id=telegram_id)
        )

        return result.scalars().one_or_none()

    async def create_user(self, telegram_id: int, **kwargs) -> User:
        user = User(telegram_id=telegram_id, **kwargs)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_user_language(self, telegram_id: int, language_code: str) -> Optional[User]:
        user = await self.get_user_by_telegram_id(telegram_id)
        if user:
            user.language_code = language_code
            await self.session.commit()
            await self.session.refresh(user)

        return user

    async def get_user_language(self, telegram_id: int) -> str:
        user = await self.get_user_by_telegram_id(telegram_id)
        return user.language_code if user else "en"


