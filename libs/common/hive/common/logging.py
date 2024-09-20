import os

from typing import Optional


def getenv_log_level() -> Optional[int | str]:
    level = os.environ.get("LL", None)
    if not level:
        return None
    try:
        return int(level)
    except ValueError:
        return level.upper()
