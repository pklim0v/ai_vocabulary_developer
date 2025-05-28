from typing import Dict, Any, Optional, List

from aiogram.types import InlineKeyboardMarkup

from developer.localization.generators import keyboards
import logging

logger = logging.getLogger(__name__)


class KeyboardGenerator:
    def __init__(self):
        # in here we register generator functions for each available locale
        self.generators = {
            'en': self._get_keyboard_generator()
        }

    def _get_keyboard_generator(self) -> Dict[str, callable]:
        return {
            'generate_numeric_keyboard': keyboards.generate_numeric_keyboard
        }

    def get_keyboard(self, key: str, locale: str, context: Dict[str, Any]) -> Optional[InlineKeyboardMarkup]:
        if locale not in self.generators:
            locale = 'en'

        generator_func = self.generators[locale].get(key)
        logger.debug(f'Generator function is {generator_func}')
        if not generator_func or not context:
            return None

        try:
            return generator_func(**context)

        except Exception as e:
            logger.debug(f'Failed to generate keyboard for {key}: {e}')
            return None

# creating global generator
keyboard_generator = KeyboardGenerator()