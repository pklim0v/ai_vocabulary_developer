from aiogram import Router, Bot
from .handlers import setup_handlers
import logging

logger = logging.getLogger(__name__)

async def init_registration_router(bot: Bot) -> Router:
    try:
        router = Router()
        await setup_handlers(router, bot)
        return router

    except Exception as e:
        logger.error(f"Error initializing the Registration router: {e}")
        raise