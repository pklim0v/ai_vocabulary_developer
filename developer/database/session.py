from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from config import get_config

logger = logging.getLogger(__name__)
Config = get_config()

# create Base for models
Base = declarative_base()

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.async_session_maker = None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            logger.warning("Database already initialized")
            return

        try:
            # create db engine
            self.engine = create_async_engine(
                Config.DATABASE_URI,
                echo=Config.DEBUG,
                future=True,
                pool_pre_ping=True,
                pool_recycle=3600
            )

            # create async session maker
            self.async_session_maker = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )

            self._initialized = True
            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing the database: {e}")
            raise

    async def create_tables(self):
        if not self._initialized:
            await self.initialize()

        try:
            from developer.database.models import Base
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Tables created successfully")

        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    async def drop_tables(self):
        if not self._initialized:
            await self.initialize()

        try:
            from developer.database.models import Base
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("Tables dropped successfully")

        except Exception as e:
            logger.error(f'Failed to drop database tables: {e}')
            raise

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        if not self._initialized:
            await self.initialize()

        async with self.async_session_maker() as session:
            try:
                yield session

            except Exception as e:
                await session.rollback()
                logger.error(f"Error while processing a database request: {e}")
                raise

            finally:
                await session.close()

    async def close(self):
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")

        self._initialized = False

db_manager = DatabaseManager()

async def initialize_database():
    logger.info("Initializing database")
    await db_manager.initialize()

    logger.info("Creating tables")
    logger.debug(f'{Config.DATABASE_URI}')
    await db_manager.create_tables()

async def close_database():
    await db_manager.close()

async def reset_database():
    if not Config.TESTING:
        raise RuntimeError("Resetting database is only allowed in testing mode")

    await db_manager.drop_tables()
    await db_manager.create_tables()
    logger.info("Database reset successfully")
