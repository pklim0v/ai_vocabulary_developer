import re
from typing import Optional


class Validator:
    @staticmethod
    def validate_username(username: str) -> Optional[str]:
        return username if re.match(r'^@[a-zA-Z0-9_]{3,32}$', username) else None