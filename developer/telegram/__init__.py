from config import get_config
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from .routers import init_routers
import logging

# setting up logging
logger = logging.getLogger(__name__)

# getting config
Config = get_config()

# initial telegram parameters
developer_bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
storage = MemoryStorage()
developer_dispatcher = Dispatcher(storage=storage)

# initialize telegram bot
async def initialize_telegram_bot():
    try:
        await init_routers(developer_bot, developer_dispatcher)
        logger.info("Telegram bot initialized")

        if Config.WEBHOOK_ENABLED:
            await developer_bot.delete_webhook(drop_pending_updates=True)
            await developer_bot.set_webhook(
                url=f'{Config.WEBHOOK_URL}{Config.WEBHOOK_PATH}',
                drop_pending_updates=True
            )
            logger.info(f"Telegram bot set up with webhook to {Config.WEBHOOK_URL}{Config.WEBHOOK_PATH}")
        else:
            await developer_bot.delete_webhook(drop_pending_updates=True)
            logger.info('Webhook disabled, using polling')

    except Exception as e:
        logger.error(f"Error initializing the telegram bot: {e}")
        raise
