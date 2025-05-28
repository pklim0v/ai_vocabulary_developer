import json
import locale
import os
from typing import Any, Dict, Optional
from pathlib import Path
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .text_generators import text_generators
from .keyboard_generators import keyboard_generator
import logging

logger = logging.getLogger(__name__)


class Localization:
    """
    Handles multi-language support by managing localization data and retrieving
    translated text based on locale and key.

    The `Localization` class is designed to load localization files, store their
    content, and retrieve the localized text for a given key. It handles nested keys
    and provides fallback to a default locale if the translation is unavailable in
    the requested locale. It's primarily used in applications requiring multi-language
    support.

    :ivar locales: A dictionary containing localization data for different languages.
                   Each key represents the locale name, and the value is another
                   dictionary containing text translations.
    :type locales: Dict[str, Dict[str, Any]]
    :ivar default_locale: The fallback locale to use when a specified locale or
                          translation key is unavailable.
    :type default_locale: str
    """
    def __init__(self) -> None:
        self.locales: Dict[str, Dict[str, Any]] ={}
        self.default_locale = "en"
        self._load_locales()

    def _load_locales(self) -> None:
        locale_dir = Path(__file__).parent / "locales"

        if not locale_dir.exists():
            raise FileNotFoundError(f"No locales directory found at {locale_dir}")
            return

        for locale_file in locale_dir.glob("*.json"):
            try:
                locale_name = locale_file.stem
                with open(locale_file, "r", encoding="utf-8") as f:
                    self.locales[locale_name] = json.load(f)
                logger.debug(f"Loaded locale '{locale_name}'")

            except Exception as e:
                logger.error(f"Failed to load locale '{locale_name}': {e}")
                raise

    def get_text(self, key: str, locale: str = None, **kwargs) -> str:
        if locale is None:
            locale = self.default_locale

        if locale not in self.locales:
            locale = self.default_locale

        static_text = self._get_static_text(key, locale, **kwargs)
        if static_text is not None:
            return static_text

        dynamic_text = self._get_dynamic_text(key, locale, **kwargs)
        if dynamic_text is not None:
            return dynamic_text

        return f'Missing text for {key}'

    def _get_static_text(self, key: str, locale: str, **kwargs) -> Optional[str]:
        text = self._get_nested_value(self.locales[locale], key)

        if text is None and locale != self.default_locale:
            text = self._get_nested_value(self.locales[self.default_locale], key)

        try:
            if text is None:
                logger.debug(f"Text with key '{key}' not found in locale '{locale}'")
                return text

            else:
                logger.debug(f"Text with key '{key}' found in locale '{locale}'")
                return text.format(**kwargs) if kwargs else text

        except KeyError as e:
            raise ValueError(f"Missing argument for text '{key}': {e}")

    def _get_dynamic_text(self, key: str, locale: str, **kwargs) -> Optional[str]:
        return text_generators.get_text(key, locale, kwargs)

    def _get_nested_value(self, data: dict, key: str) -> Any:
        if not data:
            return None

        keys = key.split(".")
        current = data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]

            else:
                return None

        return current

    def get_keyboard(self, key: str, locale: str = None, **kwargs) -> InlineKeyboardMarkup:
        if locale is None:
            locale = self.default_locale

        if locale not in self.locales:
            locale = self.default_locale

        static_keyboard = self._get_static_keyboard(key, locale, **kwargs)
        if static_keyboard is not None:
            return static_keyboard

        dynamic_keyboard = self._get_dynamic_keyboard(key, locale, **kwargs)
        if dynamic_keyboard is not None:
            return dynamic_keyboard

        return InlineKeyboardMarkup()

    def _get_static_keyboard(self, key: str, locale: str, **kwargs) -> Optional[InlineKeyboardMarkup]:
        keyboard = self._get_nested_keyboard(self.locales[locale], key)

        if keyboard is None and locale != self.default_locale:
            keyboard = self._get_nested_keyboard(self.locales[self.default_locale], key)

        try:
            if keyboard is None:
                logger.debug(f"Keyboard with key '{key}' not found in locale '{locale}'")
                return keyboard

            else:
                logger.debug(f"Keyboard with key '{key}' found in locale '{locale}'")
                return keyboard

        except KeyError as e:
            raise ValueError(f"Missing argument for keyboard '{key}': {e}")

    def _get_nested_keyboard(self, data: dict, key: str) -> Optional[InlineKeyboardMarkup]:
        if not data:
            return None

        keys = key.split(".")
        current = data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]

            else:
                return None

        logger.debug(f"Keyboard with key '{key}' found in locale '{locale}: {current}'")
        keyboard_buttons = []
        ordered_buttons = []

        try:
            for button in current['buttons']:
                keyboard_buttons.append(InlineKeyboardButton(
                    text=current['buttons'][button]['label'],
                    callback_data=current['buttons'][button]['callback_data']))

            for i in range(0, len(keyboard_buttons), current['buttons_per_row']):
                ordered_buttons.append(keyboard_buttons[i:i+current['buttons_per_row']])

        except KeyError as e:
            logger.error(f"Missing argument for keyboard '{key}': {e}")
            return None

        return InlineKeyboardMarkup(inline_keyboard=ordered_buttons)

    def _get_dynamic_keyboard(self, key: str, locale: str, **kwargs) -> Optional[InlineKeyboardMarkup]:
        return keyboard_generator.get_keyboard(key, locale, kwargs)


# creating global
i18n = Localization()
