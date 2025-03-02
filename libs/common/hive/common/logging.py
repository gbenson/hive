import os

from typing import Optional, TypeAlias

LogLevel: TypeAlias = int | str


def getenv_log_level(default: Optional[LogLevel] = None) -> Optional[LogLevel]:
    if default is not None:
        default = str(default)

    level = os.environ.get("LL", default)
    if not level:
        return None
    try:
        return int(level)
    except ValueError:
        return level.upper()
