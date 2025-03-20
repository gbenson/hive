from datetime import datetime, timezone
from functools import partial


def parse_datetime(s: str) -> datetime:
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        if not s.endswith("Z"):
            raise
    return datetime.fromisoformat(f"{s[:-1]}+00:00")


utc_now = partial(datetime.now, tz=timezone.utc)
utc_now.__doc__ = """\
Return the current UTC date and time as an aware `datetime` object.
"""
