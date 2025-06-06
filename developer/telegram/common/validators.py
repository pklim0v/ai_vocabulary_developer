import re
import regex
import unicodedata
from typing import Optional


class Validator:
    USERNAME_PATTERN = regex.compile(r'^[\p{L}\p{N}\s\-\._]{3,32}$', regex.UNICODE)

    @staticmethod
    def validate_username(username: str) -> Optional[str]:

        # primary check of existence and instance
        if not username or not isinstance(username, str):
            return None

        # Unicode normalization
        username = unicodedata.normalize('NFC', username.strip())

        # comprehensive check
        if not Validator.USERNAME_PATTERN.match(username):
            return None

        elif '\x00' in username or '\n' in username or '\r' in username:
            return None

        return username


