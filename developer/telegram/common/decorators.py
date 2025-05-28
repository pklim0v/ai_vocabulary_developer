from functools import wraps
from aiogram import types
from developer.localization import i18n
from developer.services.user_service import UserService
from developer.database.session import db_manager


def with_localization(handler):
    """
    Applies localization based on the user's language settings in the
    context of a message or callback interaction.

    The decorator applies logic to fetch the user's language and provides
    a localized text function (`t`) to the wrapped handler function. If
    the user's language is available, it is used for localization. Otherwise,
    it defaults to English ('en').

    :param handler: The asynchronous handler function to be wrapped,
        which processes the message or callback interaction and optionally
        uses the localization function provided.
    :return: The wrapped handler function with added localization support,
        including providing a `t` function for fetching translated strings.
    """
    @wraps(handler)
    async def wrapper(message_or_callback, *args, **kwargs):
        if isinstance(message_or_callback, types.Message):
            user_id = message_or_callback.from_user.id

        if isinstance(message_or_callback, types.CallbackQuery):
            user_id = message_or_callback.from_user.id

        else:
            def t(key: str, locale = 'en', **format_kwargs):
                return i18n.get_text(key, locale, **format_kwargs)

            def k(key: str, locale = 'en', **format_kwargs):
                return i18n.get_keyboard(key, locale, **format_kwargs)

            return await handler(message_or_callback, t, k, *args, **kwargs)

        async with db_manager.get_session() as session:
            user_service = UserService(session)
            user_language = await user_service.get_user_language(user_id)

        def t(key: str, **format_kwargs):
            return i18n.get_text(key, user_language, **format_kwargs)

        def k(key: str, **format_kwargs):
            return i18n.get_keyboard(key, user_language, **format_kwargs)

        return await handler(message_or_callback, t, k, *args, **kwargs)

    return wrapper

def with_localization_and_state(handler):
    """
    Decorator function designed to add localization and state management
    to an asynchronous handler function. It utilizes user-specific language
    settings and enhances the functionality of the handler by injecting
    a translation function (`t`) into its execution.

    :param handler: The asynchronous function (or coroutine) to be wrapped.
        This handler will be executed with additional functionality for
        localization and state access.
    :return: Returns the wrapped handler function that includes logic for
        retrieving the user's language and providing a translation function
        (`t`).
    """
    @wraps(handler)
    async def wrapper(message_or_callback, state, *args, **kwargs):
        if isinstance(message_or_callback, types.Message):
            user_id = message_or_callback.from_user.id

        elif isinstance(message_or_callback, types.CallbackQuery):
            user_id = message_or_callback.from_user.id

        else:
            def t(key: str, locale = 'en', **format_kwargs):
                return i18n.get_text(key, locale, **format_kwargs)

            def k(key: str, locale = 'en', **format_kwargs):
                return i18n.get_keyboard(key, locale, **format_kwargs)

            return await handler(message_or_callback, state, t, k, *args, **kwargs)

        async with db_manager.get_session() as session:
            user_service = UserService(session)
            user_language = await user_service.get_user_language(user_id)

        def t(key: str, **format_kwargs):
            return i18n.get_text(key, user_language, **format_kwargs)

        def k(key: str, **format_kwargs):
            return i18n.get_keyboard(key, user_language, **format_kwargs)

        return await handler(message_or_callback, state, t, k, *args, **kwargs)

    return wrapper

def admin_required(handler):
    @wraps(handler)
    async def wrapper(message_or_callback, *args, **kwargs):
        if isinstance(message_or_callback, types.Message):
            user_id = message_or_callback.from_user.id

        elif isinstance(message_or_callback, types.CallbackQuery):
            user_id = message_or_callback.from_user.id