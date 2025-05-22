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

    async def check_migration_status(self):
        if not self._initialized:
            await self.initialize()

        try:
            from alembic.config import Config as AlembicConfig
            from alembic import command
            from alembic.script import ScriptDirectory
            from alembic.runtime.migration import MigrationContext

            alembic_cfg = AlembicConfig('alembic.ini')
            alembic_cfg.set_main_option('sqlalchemy.url', Config.DATABASE_URI)

            script = ScriptDirectory.from_config(alembic_cfg)

            def get_migration_info(sync_conn):
                context = MigrationContext.configure(sync_conn)
                current_revision = context.get_current_revision()
                return current_revision

            async with self.engine.connect() as connection:
                current_revision = await connection.run_sync(get_migration_info)
                head_revision = script.get_current_head()

                if current_revision != head_revision:
                    logger.warning(f"Database is not up to date. Current revision: {current_revision}, head revision: {head_revision}")
                    return False
                else:
                    logger.info("Database is up to date")
                    return True

        except Exception as e:
            logger.error(f"Error checking migration status: {e}")
            raise

db_manager = DatabaseManager()

async def initialize_database():
    # initialize database
    logger.info("Initializing database")
    await db_manager.initialize()

    # check migration status
    logger.info("Checking migration status")
    migrations_ok = await db_manager.check_migration_status()
    if not migrations_ok:
        if Config.__class.__name__ == 'ProductionConfig':
            raise RuntimeError("Database is not up to date. Please run 'alembic upgrade head' to upgrade the database.")
        else:
            logger.warning("Database is not up to date. Please run 'alembic upgrade head' to upgrade the database.")

    # create tables
    logger.info("Creating tables")
    await db_manager.create_tables()

async def close_database():
    await db_manager.close()

async def reset_database():
    if not Config.TESTING:
        raise RuntimeError("Resetting database is only allowed in testing mode")

    await db_manager.drop_tables()
    await db_manager.create_tables()
    logger.info("Database reset successfully")
