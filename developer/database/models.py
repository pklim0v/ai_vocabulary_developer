from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import UniqueConstraint, Index

from .session import Base


# table for many-to-many relations of users learning languages and learning languages
user_learning_languages = Table(
    'user_learning_languages',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('language_id', Integer, ForeignKey('languages.id'), primary_key=True),
    Column('started_learning_at', DateTime, server_default=func.now(), nullable=False),
    Column('finished_learning_at', DateTime, nullable=True),
    Column('is_active', Boolean, nullable=False, default=False),
)


class User(Base):
    __tablename__ = "users"

    # user common data
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(32), nullable=False)
    # language_code = Column(String(10), nullable=False, default="en")
    interface_language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    time_format = Column(Integer, nullable=False, default=24)
    timezone = Column(String(256), nullable=False, default="UTC")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # terms_of_usage data
    agreed_to_terms_of_service = Column(Boolean, nullable=False, default=False)
    accepted_agreement_id = Column(Integer, ForeignKey("user_agreements.id"), nullable=True)
    agreement_accepted_at = Column(DateTime, nullable=True)
    accepted_privacy_policy_id = Column(Integer, ForeignKey("privacy_policies.id"), nullable=True)
    policy_accepted_at = Column(DateTime, nullable=True)

    # user-bot relations data
    is_admin = Column(Boolean, nullable=False, default=False)
    is_confirmed = Column(Boolean, nullable=False, default=False)
    confirmed_admin_id = Column(Integer, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)

    # bot's community data
    agreed_to_accept_users_words = Column(Boolean, nullable=False, default=False)
    agreed_to_share_own_words = Column(Boolean, nullable=False, default=False)
    agreed_to_share_telegram_link = Column(Boolean, nullable=False, default=False)
    agreed_to_participate_in_challenges = Column(Boolean, nullable=False, default=False)

    # subscription data
    is_always_free_of_charge = Column(Boolean, nullable=False, default=False)
    trial_starts_at = Column(DateTime, nullable=True)
    trial_ends_at = Column(DateTime, nullable=True)
    payment_confirmed = Column(Boolean, nullable=False, default=False)
    subscription_type = Column(String(20), nullable=True)
    subscription_starts_at = Column(DateTime, nullable=True)
    subscription_ends_at = Column(DateTime, nullable=True)
    subscription_autorenew = Column(Boolean, nullable=False, default=False)
    subscription_cancelled_at = Column(DateTime, nullable=True)

    # relationships
    tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")
    words = relationship("Word", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")

    # relationships with user agreements and privacy policies
    accepted_agreement = relationship("UserAgreement", foreign_keys="User.accepted_agreement_id", post_update=True)
    accepted_privacy_policy = relationship("PrivacyPolicy", foreign_keys="User.accepted_privacy_policy_id", post_update=True)

    # relationships for agreements and privacy policies administration
    activated_agreements = relationship("UserAgreement", foreign_keys="UserAgreement.activated_by_id", back_populates="activated_by")
    activated_privacy_policies = relationship("PrivacyPolicy", foreign_keys="PrivacyPolicy.activated_by_id", back_populates="activated_by")
    deactivated_agreements = relationship("UserAgreement", foreign_keys="UserAgreement.deactivated_by_id", back_populates="deactivated_by")
    deactivated_privacy_policies = relationship("PrivacyPolicy", foreign_keys="PrivacyPolicy.deactivated_by_id", back_populates="deactivated_by")

    # property for receiving language_code
    # many-to-one
    interface_language = relationship("Language", back_populates="interface_users")

    @property
    def language_code(self):
        return self.interface_language.code if self.interface_language else "en"

    # relationship for studying languages
    # many-to-many
    learning_languages = relationship(
        "Language",
        secondary=user_learning_languages,
        back_populates="learning_users",
    )

    # receiving interface language name in the current locale
    def get_interface_language_name(self, locale_code: str = "en") -> str:
        if not self.interface_language:
            return "Unknown"

        if locale_code is None:
            locale_code = self.language_code

        return self.interface_language.get_name(locale_code)


    def __repr__(self):
        return f"<User(id={self.id}, name={self.username}, telegram_id={self.telegram_id})>"


class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), nullable=False, unique=True, index=True)
    is_interface_language = Column(Boolean, nullable=False, default=False)
    flag_code = Column(String(10), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # relationships for interface language
    # one-to-many
    interface_users = relationship("User", back_populates="interface_language")

    # relationships for studying languages
    # many-to-many
    learning_users = relationship(
        "User",
        secondary=user_learning_languages,
        back_populates="learning_languages"
    )

    # relationships for user agreements and privacy policies
    # one-to-many
    agreements = relationship("UserAgreement", back_populates="agreement_language")
    privacy_policies = relationship("PrivacyPolicy", back_populates="policy_language")

    # relationship for localization
    # one-to-many
    translations = relationship("LanguageTranslation",
                                foreign_keys="LanguageTranslation.language_id",
                                back_populates="language",
                                cascade="all, delete-orphan")

    # getting language name in the current locale
    def get_name(self, locale_code: str = "en") -> str:
        for translation in self.translations:
            if translation.locale and translation.locale.code == locale_code:
                return translation.name

        # Fallback to English and then first available translation
        for translation in self.translations:
            if translation.locale and translation.locale.code == "en":
                return translation.name

        if self.translations:
            return self.translations[0].name

        return self.code.upper() # last Fallback


    def __repr__(self):
        return f"<Language(id={self.id}, name={self.name}, code={self.code})>"



class LanguageTranslation(Base):
    __tablename__ = "language_translations"

    __table_args__ = (
        UniqueConstraint('language_id', 'locale_id', name='unique_language_translation_language_id_locale_id'),
        UniqueConstraint('language_id', 'name', name='unique_language_translation_language_id_name'),
    )

    id = Column(Integer, primary_key=True)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False, index=True)
    locale_id = Column(Integer, ForeignKey("languages.id"), nullable=False, index=True)
    name = Column(String(32), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # relationships for localization
    # many-to-one
    language = relationship("Language",
                            foreign_keys=[language_id],
                            back_populates="translations")

    locale = relationship("Language",
                          foreign_keys=[locale_id])

    # localization code for backward compatibility
    @property
    def locale_code(self):
        return self.locale.code if self.locale else "en"

    def __repr__(self):
        return (f"<LanguageTranslation(id={self.id},"
                f" language_id={self.language_id},"
                f" locale_id={self.locale_id},"
                f" name={self.name},"
                f" created_at={self.created_at})>")


class UserAgreement(Base):
    __tablename__ = "user_agreements"

    __table_args__ = (
        UniqueConstraint('version', 'agreement_language_id', name='unique_agreement_version_language_id'),
    )

    id = Column(Integer, primary_key=True)
    version = Column(String(10), nullable=False)
    agreement_language_id = Column(Integer, ForeignKey('languages.id'), nullable=False, index=True)
    url = Column(String(256), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    is_active = Column(Boolean, nullable=False, default=False, index=True)
    activated_at = Column(DateTime, nullable=True)
    activated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    deactivated_at = Column(DateTime, nullable=True)
    deactivated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # relationships for administration
    activated_by = relationship("User", foreign_keys="UserAgreement.activated_by_id", back_populates="activated_agreements")
    deactivated_by = relationship("User", foreign_keys="UserAgreement.deactivated_by_id", back_populates="deactivated_agreements")

    # users who accepted the agreement
    users = relationship("User", foreign_keys="User.accepted_agreement_id", back_populates="accepted_agreement")

    # localization relationship
    # many-to-one
    agreement_language = relationship("Language", back_populates="agreements")

    # property for receiving language_code
    @property
    def language_code(self):
        return self.agreement_language.code if self.agreement_language else "en"

    def __repr__(self):
        return f"<UserAgreements(id={self.id}, version={self.version}, url={self.url}, created_at={self.created_at}, " \
               f"is_active={self.is_active}, activated_at={self.activated_at}, deactivated_at={self.deactivated_at})>"


class PrivacyPolicy(Base):
    __tablename__ = "privacy_policies"

    __table_args__ = (
        UniqueConstraint('version', 'policy_language_id', name='unique_privacy_policy_version_language_id'),
    )

    id = Column(Integer, primary_key=True)
    version = Column(String(10), nullable=False)
    policy_language_id = Column(Integer, ForeignKey('languages.id'), nullable=False, index=True)
    url = Column(String(256), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    is_active = Column(Boolean, nullable=False, default=False, index=True)
    activated_at = Column(DateTime, nullable=True)
    activated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    deactivated_at = Column(DateTime, nullable=True)
    deactivated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # relationships for administration
    activated_by = relationship("User", foreign_keys="PrivacyPolicy.activated_by_id", back_populates="activated_privacy_policies")
    deactivated_by = relationship("User", foreign_keys="PrivacyPolicy.deactivated_by_id", back_populates="deactivated_privacy_policies")

    # users who accepted the privacy policy
    users = relationship("User", foreign_keys="User.accepted_privacy_policy_id", back_populates="accepted_privacy_policy")

    # relationship for localization
    # many-to-one
    policy_language = relationship("Language", back_populates="privacy_policies")

    # property for receiving language_code
    @property
    def language_code(self):
        return self.policy_language.code if self.policy_language else "en"


    def __repr__(self):
        return f"<PrivacyPolicies(id={self.id}, version={self.version}, url={self.url}, created_at={self.created_at}, " \
               f"is_active={self.is_active}, activated_at={self.activated_at}, deactivated_at={self.deactivated_at})>"


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    word = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


    #relationships
    user = relationship("User", back_populates="words")

    def __repr__(self):
        return f"<Word(id={self.id}, word={self.word}, user_id={self.user_id})>"


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    token_count = Column(Integer, nullable=False, default=0)
    cost = Column(Float, nullable=False, default=0.0)

    #relationships
    user = relationship("User", back_populates="tokens")

    def __repr__(self):
        return f"<Token(id={self.id}, user_id={self.user_id})>"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String(20), nullable=False)
    payment_id = Column(String(256), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="RUB")
    subscription_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    #relationships
    user = relationship("User", back_populates="payments")

    def __repr__(self):
        return (f"<Payment(id={self.id}, user_id={self.user_id}, payment_id={self.payment_id},"
                f" amount={self.amount}, currency={self.currency}, subscription_type={self.subscription_type},"
                f" status={self.status}, created_at={self.created_at}, completed_at={self.completed_at})>")


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False, unique=True)
    discount_percent = Column(Integer, nullable=False, default=0)
    discount_amount = Column(Float, nullable=False, default=0.0)
    uses_limit = Column(Integer, nullable=True)
    uses_count = Column(Integer, nullable=False, default=0)
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<PromoCode(id={self.id}, code={self.code}, discount_percent={self.discount_percent}," \
               f" discount_amount={self.discount_amount}, uses_limit={self.uses_limit}, " \
               f"uses_count={self.uses_count}, valid_from={self.valid_from}, valid_until={self.valid_until}, " \
               f"is_active={self.is_active}, created_at={self.created_at})>"