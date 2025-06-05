from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from developer.database.models import PrivacyPolicy
from typing import Optional

class PrivacyPolicyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session