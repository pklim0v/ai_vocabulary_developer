from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
import os
from config import get_config

from developer import initialize_application

Config = get_config()

def logging_setup():
    if Config.LOG_LEVEL == "DEBUG":
        logging.basicConfig(
            level=logging.DEBUG,
            format=Config.LOG_FORMAT,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('./logs/app.log', 'a', 'utf-8') if not Config.TESTING else logging.NullHandler()
            ]
        )

    else:
        logging.basicConfig(
            level=logging.INFO,
            format=Config.LOG_FORMAT,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('./logs/app.log', 'a', 'utf-8')
            ]
        )

logger = logging.getLogger(__name__)


async def validate_config():
    required_config_keys = ['CLAUDE_API_TOKEN', 'TELEGRAM_BOT_TOKEN', 'DATABASE_URI', 'LOG_LEVEL']

    missed_keys = []
    for key in required_config_keys:
        if not getattr(Config, key):
            missed_keys.append(key)

    if missed_keys:
        raise ValueError(f"Required config keys are missing: {missed_keys}")

    #for production
    if Config.__name__ == 'ProductionConfig':
        if Config.WEBHOOK_ENABLED and not Config.WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL is required for production environment with WEBHOOK_ENABLED enabled")


    logger.info(f"Config validation passed for {Config.__name__}")


async def main():
    env = os.environ.get('BOT_ENV', 'development')
    logger.info(f'Starting the bot in {env} environment with config: {Config.__name__}')
    await initialize_application()

if __name__ == '__main__':
    # setting up logging
    logger.info("Setting up logging")
    logging_setup()
    logger.info("Logging setup complete")

    #validating config
    logger.info("Validating config")
    try:
        asyncio.run(validate_config())

    except Exception as e:
        logger.error(f"Config validation failed: {e}")
        exit(1)

    # running bot
    try:
        asyncio.run(main())

    except Exception as e:
        logger.error(f"An error occurred while initializing the application: {e}")
        exit(1)



