from aiogram import types, Router, Bot
from aiogram.filters import Command


async def setup_handlers(router: Router, bot: Bot) -> None:
    @router.message(Command(commands=["start"]))
    async def start_command(message: types.Message):
        await message.answer("Hello!")