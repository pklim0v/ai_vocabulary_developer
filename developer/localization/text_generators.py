from typing import Dict, Any, Optional
from developer.localization.generators import ru, en
import logging

logger = logging.getLogger(__name__)

class TextGenerators:
    def __init__(self):
        # in here we register generator functions for each available locale
        self.generators = {
            'en': self._get_english_generators(),
            'ru': self._get_russian_generators()
        }

    def _get_english_generators(self) -> Dict[str, callable]:
        return {
            'generate_welcome_message': en.generate_welcome_message
        }

    def _get_russian_generators(self) -> Dict[str, callable]:
        return {
            'generate_welcome_message': ru.generate_welcome_message
        }

    def get_text(self, key: str, locale: str, context: Dict[str, Any] = None) -> Optional[str]:
        if locale not in self.generators:
            locale = 'en'

        generator_func = self.generators[locale].get(key)
        logger.debug(f'Generator function is {generator_func}')
        if not generator_func or not context:
            return None

        try:
            return generator_func(**context)

        except Exception as e:
            logger.debug(f'Failed to generate text for {key}: {e}')
            return None


# creating global generator
text_generators = TextGenerators()
