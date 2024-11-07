from __future__ import annotations

from enum import Enum
from typing import Optional


class Route(Enum):
    LOGIN = "/login"
    EVENTS = "/events"
    CHAT = "/chat"

    @classmethod
    def from_path(cls, path) -> Optional[Route]:
        try:
            return cls(path)
        except ValueError:
            return None
