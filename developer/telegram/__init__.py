from config import Config
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from .routers import init_routers
import logging

# setting up logging
logger = logging.getLogger(__name__)

# iniitial telegram parameters
developer_bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
storage = MemoryStorage()
developer_dispatcher = Dispatcher(storage=storage)

# initialize telegram bot
async def initialize_telegram_bot():
    try:
        await init_routers(developer_bot, developer_dispatcher)
        logger.info("Telegram bot initialized")
        await developer_bot.delete_webhook(drop_pending_updates=True)

    except Exception as e:
        logger.error(f"Error initializing the telegram bot: {e}")
