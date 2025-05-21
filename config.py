import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    CLAUDE_API_TOKEN = os.environ.get('CLAUDE_API_TOKEN')
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    LOG_LEVEL = os.environ.get('LOG_LEVEL')

    DATABASE_URI=f'sqlite+aiosqlite://{BASE_DIR}/database/database.sql'
