from aiogram import Bot, Dispatcher
from .CommonRouter import init_common_router
from .RegistrationRouter import init_registration_router

import logging
logger = logging.getLogger(__name__)

async def init_routers(bot: Bot, dispatcher: Dispatcher) -> None:
    #initializing the common router
    try:
        dispatcher.include_router(await init_common_router(bot))
        logger.debug("Common router initialized")

    except Exception as e:
        logger.error(f"Error initializing the common router: {e}")

    #initializong the registration router
    try:
        dispatcher.include_router(await init_registration_router(bot))
        logger.debug("Registration router initialized")

    except Exception as e:
        logger.error(f"Error initializing the Registration router: {e}")


