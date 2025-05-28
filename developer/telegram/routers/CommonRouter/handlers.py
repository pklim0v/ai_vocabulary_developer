from aiogram import types, Router, Bot
from aiogram.filters import Command
from developer.telegram.common.decorators import with_localization


async def setup_handlers(router: Router, bot: Bot) -> None:
    @router.message(Command(commands=["start"]))
    @with_localization
    async def start_command(message: types.Message, t):
        await message.answer("Hello!")

    @router.message(Command(commands=['test1']))
    @with_localization
    async def test1_command(message: types.Message, t):
        await message.answer(t('commands.start'))

    @router.message(Command(commands=['test2']))
    @with_localization
    async def test2_command(message: types.Message, t):
        context = {
            'name': message.from_user.username,
            'telegram_id': message.from_user.id
        }
        await message.answer(t('generate_welcome_message', context=context))