from datetime import datetime


def parse_datetime(s: str) -> datetime:
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        if not s.endswith("Z"):
            raise
    return datetime.fromisoformat(f"{s[:-1]}+00:00")
