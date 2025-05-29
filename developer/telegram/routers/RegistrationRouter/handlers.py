from aiogram import types, Router, Bot
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from developer.telegram.common.decorators import with_localization
from developer.services import UserService
from developer.database.session import db_manager
import logging

logger = logging.getLogger(__name__)

class RegistrationState(StatesGroup):
    name = State()


async def setup_handlers(router: Router, bot: Bot) -> None:
    @router.callback_query(lambda c: c.data == "register")
    @with_localization
    async def registration_start(callback_query: types.CallbackQuery, t, k):
        await bot.answer_callback_query(callback_query.id)

        # deleting the keyboard
        await callback_query.message.edit_reply_markup(reply_markup=None)

        await bot.send_message(callback_query.from_user.id, t("commands.start"))