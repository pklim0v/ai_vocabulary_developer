from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(32), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    language_code = Column(String(10), nullable=False, default="en")
    is_admin = Column(Boolean, nullable=False, default=False)
    is_confirmed = Column(Boolean, nullable=False, default=False)
    is_always_free_of_charge = Column(Boolean, nullable=False, default=False)
    payment_confirmed = Column(Boolean, nullable=False, default=False)
    agreed_to_terms_of_service = Column(Boolean, nullable=False, default=False)
    agreed_to_accept_users_words = Column(Boolean, nullable=False, default=False)
    agreed_to_share_own_words = Column(Boolean, nullable=False, default=False)
    agreed_to_share_telegram_link = Column(Boolean, nullable=False, default=False)
    agreed_to_participate_in_challenges = Column(Boolean, nullable=False, default=False)
    timezones = Column(String(256), nullable=False, default="UTC")

    # relationships
    tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")
    words = relationship("Word", back_populates="user", cascade="all, delete-orphan")


    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, telegram_id={self.telegram_id})>"


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