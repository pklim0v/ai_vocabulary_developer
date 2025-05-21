from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
from config import Config

from developer import initialize_application

def logging_setup():
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    if Config.LOG_LEVEL == "DEBUG":
        logging.basicConfig(level=logging.DEBUG, format=log_format)

    else:
        logging.basicConfig(level=logging.INFO, format=log_format)


logger = logging.getLogger(__name__)


async def validate_config():
    if not Config.CLAUDE_API_TOKEN:
        raise ValueError("CLAUDE_API_TOKEN is not set")
    elif not Config.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set")
    elif not Config.DATABASE_URI:
        raise ValueError("DATABASE_URI is not set")
    elif not Config.LOG_LEVEL:
        raise ValueError("LOG_LEVEL is not set")
    else:
        logger.info("Config validation passed")


async def main():
    await initialize_application()

if __name__ == '__main__':

    #validating config
    logger.info("Validating config")
    try:
        asyncio.run(validate_config())

    except Exception as e:
        logger.error(f"Config validation failed: {e}")

    #setting up logging
    logger.info("Setting up logging")
    logging_setup()
    logger.info("Logging setup complete")

    try:
        asyncio.run(main())

    except Exception as e:
        logger.error(f"An error occurred while initializing the application: {e}")



