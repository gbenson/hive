from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from types import NoneType
from typing import Any, Optional
from uuid import RFC_4122, UUID, uuid4


@dataclass
class ChatMessage:
    text: Optional[str] = None
    html: Optional[str] = None
    sender: str = "hive"
    timestamp: str | datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc))
    uuid: str | UUID = field(default_factory=uuid4)
    _unhandled: Optional[dict[str, Any]] = field(default=None, repr=False)

    def __post_init__(self):
        if not self.text and not self.html:
            raise ValueError
        if not isinstance(self.text, (str, NoneType)):
            raise TypeError(type(self.text))
        if not isinstance(self.html, (str, NoneType)):
            raise TypeError(type(self.html))

        if not isinstance(self.sender, str):
            raise TypeError(type(self.sender))

        if not isinstance(self.timestamp, datetime):
            self.timestamp = datetime.fromisoformat(self.timestamp)

        if not isinstance(self.uuid, UUID):
            self.uuid = UUID(self.uuid)

        if self.uuid.variant != RFC_4122:
            raise ValueError(self.uuid)
        if self.uuid.version != 4:
            raise ValueError(self.uuid)

    @classmethod
    def json_keys(cls) -> list[str]:
        names = (field.name for field in fields(cls))
        return [name for name in names if name[0] != "_"]

    @classmethod
    def from_json(cls, message: dict[str, Any]) -> ChatMessage:
        """Ultra-strict from-(deserialized)-JSON constructor.
        """
        if type(message) is not dict:
            raise TypeError
        if any(type(key) is not str for key in message.keys()):
            raise TypeError
        if type(message["sender"]) is not str:
            raise TypeError

        unhandled = message.copy()
        keys = cls.json_keys()
        values = [unhandled.pop(key, None) for key in keys]
        kwargs = dict(
            item
            for item in zip(keys, values)
            if item[1] not in ("", None)
        )

        if any(type(value) is not str for value in kwargs.values()):
            raise TypeError

        if unhandled:
            kwargs["_unhandled"] = unhandled
        return cls(**kwargs)

    @property
    def has_unhandled_fields(self):
        return bool(self._unhandled)

    def json(self) -> dict[str, Any]:
        items = ((key, getattr(self, key)) for key in self.json_keys())
        return dict((key, str(value)) for key, value in items if value)
