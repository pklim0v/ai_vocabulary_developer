from aiogram import types, Router, Bot
from aiogram.filters import Command
from developer.telegram.common.decorators import with_localization
from developer.services import UserService
from developer.database.session import db_manager
import logging

logger = logging.getLogger(__name__)


async def setup_handlers(router: Router, bot: Bot) -> None:
    @router.message(Command(commands=["start"]))
    @with_localization
    async def start_command(message: types.Message, t, k):
        # looking up for the current user
        async with db_manager.get_session() as session:
            user_service = UserService(session)
            current_user = await user_service.get_user_by_telegram_id(message.from_user.id)
            logger.debug(f"Current user: {current_user}")

        # user not registered
        if not current_user:
            current_locale = message.from_user.language_code
            await message.answer(t('commands.start', locale=current_locale))
            await message.answer(
                text=t('messages.not_registered', locale=current_locale),
                reply_markup=k('keyboards.register', locale=current_locale),
                parse_mode='MarkdownV2'
            )

    @router.message(Command(commands=['test1']))
    @with_localization
    async def test1_command(message: types.Message, t, k):
        await message.answer(t('commands.start'))

    @router.message(Command(commands=['test2']))
    @with_localization
    async def test2_command(message: types.Message, t, k):
        current_locale = message.from_user.language_code
        context = {
            'name': message.from_user.username,
            'telegram_id': message.from_user.id
        }
        await message.answer(t('generate_welcome_message', locale=current_locale, context=context))

    @router.message(Command(commands=['test3']))
    @with_localization
    async def test3_command(message: types.Message, t, k):
        context = {
            'name': message.from_user.username,
            'telegram_id': message.from_user.id
        }

        await message.answer(
            text=t('generate_welcome_message', context=context),
            reply_markup=k('keyboards.time'),
            parse_mode='MarkdownV2'
        )

    @router.message(Command(commands=['test4']))
    @with_localization
    async def test4_command(message: types.Message, t, k):
        user_locale = message.from_user.language_code

        text_context = {
            'name': message.from_user.username,
            'telegram_id': message.from_user.id
        }

        keyboard_context = {
            'callback_base': 'test4',
            'buttons_in_a_row': 2,
            'buttons': {
                '1': {'label': '1'},
                '2': {'label': '2'},
                '3': {'label': '3'}
            }
        }

        await message.answer(
            text=t('generate_welcome_message', locale=user_locale, context=text_context),
            reply_markup=k('generate_numeric_keyboard', locale=user_locale, context=keyboard_context),
            parse_mode='MarkdownV2'
            )