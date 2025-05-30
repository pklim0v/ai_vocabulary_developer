from aiogram import types, Router, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from developer.telegram.common.decorators import with_localization, with_localization_and_state
from developer.services import UserService
from developer.database.session import db_manager
from config import get_config
import logging

Config = get_config()

logger = logging.getLogger(__name__)

class RegistrationState(StatesGroup):
    InterfaceLanguageSelect = State()
    ConfirmUsageTerms = State()
    GetUsername = State()
    SelectTimeFormat = State()
    GetTimezone = State()
    GetConfirmationReceiveWords = State()
    GetConfirmationShareWords = State()
    GetConfirmationShareContact = State()
    GetConfirmationParticipateInChallenges = State()
    GetFinalConfirmation = State()



async def setup_handlers(router: Router, bot: Bot) -> None:
    @router.callback_query(lambda c: c.data == "register")
    @with_localization_and_state
    async def registration_start(callback_query: types.CallbackQuery, state: FSMContext, t, k):
        # setting the state to the registration state
        await state.set_state(RegistrationState.InterfaceLanguageSelect)
        # answering the callback query
        await bot.answer_callback_query(callback_query.id)

        # deleting the keyboard
        await callback_query.message.edit_reply_markup(reply_markup=None)

        # creating a user_data dicitonary for the user
        user_data = {
            "telegram_id": callback_query.from_user.id,
        }

        # saving the user_data in the state
        await state.update_data(user_data=user_data)

        # getting locale
        current_locale = callback_query.from_user.language_code


        await bot.send_message(
            callback_query.from_user.id,
            text=t('messages.registration.language_select', locale=current_locale),
            parse_mode="MarkdownV2",
            )