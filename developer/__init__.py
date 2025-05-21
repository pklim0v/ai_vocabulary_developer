from .telegram import developer_dispatcher, developer_bot, initialize_telegram_bot
import logging

logger = logging.getLogger(__name__)

# initialization of the application
async def initialize_application():
    # bot initialization
    try:
        await initialize_telegram_bot()
        await developer_dispatcher.start_polling(developer_bot)

    except Exception as e:
        logger.error(f"Error initializing the application: {e}")