import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    CLAUDE_API_TOKEN = os.environ.get('CLAUDE_API_TOKEN')
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')


class DevelopmentConfig(Config):
    LOG_LEVEL = 'DEBUG'
    DATABASE_URI=f'sqlite+aiosqlite://{BASE_DIR}/database/database.sql'

class TestingConfig(Config):
    LOG_LEVEL = 'DEBUG'
    DATABASE_URI=f'sqlite+aiosqlite://{BASE_DIR}/database/database_test.sql'

class ProductionConfig(Config):
    LOG_LEVEL = 'INFO'
    DATABASE_URI=f'sqlite+aiosqlite://{BASE_DIR}/database/database.sql'

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}
