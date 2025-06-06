import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    # basic configuration
    CLAUDE_API_TOKEN = os.environ.get('CLAUDE_API_TOKEN')
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

    # common configuration for all environments
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # localization
    DEFAULT_LANGUAGE = 'en'
    SUPPORTED_LANGUAGES = ['en', 'ru']

    # admin functions
    INITIAL_ADMINS = os.environ.get('INITIAL_ADMINS', '').split(',')


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'
    DATABASE_URI=f'sqlite+aiosqlite:///{BASE_DIR}/developer/database/database_dev.sql?charset=utf8mb4'

    # telegram bot configuration
    POLLING_TIMEOUT = 10
    WEBHOOK_ENABLED = False

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    DATABASE_URI=f'sqlite+aiosqlite:///{BASE_DIR}/developer/database/database_test.sql?charset=utf8mb4'

    # telegram bot configuration
    POLLING_TIMEOUT = 1
    WEBHOOK_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = 'INFO'
    DATABASE_URI=os.environ.get('DATABASE_URI') or f'sqlite+aiosqlite:///{BASE_DIR}/developer/database/database.sql?charset=utf8mb4'

    #telegram bot configuration
    POLLING_TIMEOUT = 30
    WEBHOOK_ENABLED = True
    WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
    WEBHOOK_PATH = '/webhook/'

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}

def get_config():
    env = os.environ.get('BOT_ENV', 'development')
    return config.get(env, config['default'])
