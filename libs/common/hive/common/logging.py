import os

from typing import Optional


def getenv_log_level(default=None) -> Optional[int | str]:
    level = os.environ.get("LL", default)
    if not level:
        return None
    try:
        return int(level)
    except ValueError:
        return level.upper()
