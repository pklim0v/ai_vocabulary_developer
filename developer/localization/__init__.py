import json
import os
from typing import Any, Dict
from pathlib import Path


class Localization:
    def __init__(self, language: str) -> None:
        self.locales = Dict[str, Dict[str, Any]] ={}
        self.default_locale = "en"
        self._load_locales()

    def _load_locales(self) -> None:
        locale_dir = Path(__file__).parent / "locales"

        for locale_file in locale_dir.glob("*.json"):
            locale_name = locale_file.stem
            with open(locale_file, "r", encoding="utf-8") as f:
                self.locales[locale_name] = json.load(f)

    def get_text(self, key: str, locale: str = None, **kwargs) -> str:
        if locale is None:
            locale = self.default_locale

        if locale not in self.locales:
            locale = self.default_locale

        text = self._get_nested_value(self.locales[locale], key)

        if text is None and locale != self.default_locale:
            text = self._get_nested_value(self.locales[self.default_locale], key)

        if text is None:
            raise ValueError(f"Text with key '{key}' not found in locale '{locale}'")

        try:
            return text.format(**kwargs) if kwargs else text

        except KeyError as e:
            raise ValueError(f"Missing argument for text '{key}': {e}")

    def _get_nested_value(self, data: dict, key: str) -> Any:
        keys = key.split(".")
        current = data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]

            else:
                return None

        return current


# creating global
i18n = Localization()
