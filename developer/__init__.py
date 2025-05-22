from .telegram import developer_dispatcher, developer_bot, initialize_telegram_bot
from .database import initialize_database, close_database
import logging

logger = logging.getLogger(__name__)

# initialization of the application
async def initialize_application():
    # bot initialization
    try:
        await initialize_database()
        logger.info("Database initialized")

        await initialize_telegram_bot()
        await developer_dispatcher.start_polling(developer_bot)
        logger.info("Telegram bot started")

    except KeyboardInterrupt:
        logger.info("Application stopped by user")

    except Exception as e:
        logger.error(f"Error initializing the application: {e}")
        raise

    finally:
        logger.info("Closing the application")
        await close_database()
        logger.info("Database connection closed")
