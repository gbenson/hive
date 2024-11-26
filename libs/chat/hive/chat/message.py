from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from types import NoneType
from typing import Any, Optional
from uuid import UUID, uuid4

from hive.common import parse_uuid

from .matrix import ClientEvent as MatrixEvent


@dataclass
class ChatMessage:
    text: Optional[str] = None
    html: Optional[str] = None
    sender: str = "hive"
    timestamp: str | datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc))
    uuid: str | UUID = field(default_factory=uuid4)
    in_reply_to: Optional[str | UUID | ChatMessage] = None
    matrix: Optional[MatrixEvent] = None
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

        self.uuid = parse_uuid(self.uuid)

        if self.in_reply_to is not None:
            if isinstance(self.in_reply_to, ChatMessage):
                self.in_reply_to = self.in_reply_to.uuid
            self.in_reply_to = parse_uuid(self.in_reply_to)
            if self.in_reply_to == self.uuid:
                raise ValueError

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

        if any(key != "matrix" and type(value) is not str
               for key, value in kwargs.items()):
            raise TypeError

        if unhandled:
            kwargs["_unhandled"] = unhandled

        return cls(**kwargs)

    @classmethod
    def from_matrix_event(
            cls,
            event: MatrixEvent | dict[str, Any],
    ) -> ChatMessage:
        if not isinstance(event, MatrixEvent):
            event = MatrixEvent(event)

        if event.event_type != "m.room.message":
            raise ValueError(event.event_type)

        content = event.content
        if content.msgtype != "m.text":
            raise ValueError(content.msgtype)

        kwargs = {
            "text": content.body,
            "sender": "hive" if event.sender.startswith("@hive") else "user",
            "timestamp": event.timestamp,
            "matrix": event,
        }

        if content.format == "org.matrix.custom.html":
            kwargs["html"] = content.formatted_body

        return cls(**kwargs)

    @property
    def has_unhandled_fields(self):
        return bool(self._unhandled)

    def json(self) -> dict[str, Any]:
        items = ((key, getattr(self, key)) for key in self.json_keys())
        return dict(
            (key, value.json() if key == "matrix" else str(value))
            for key, value in items
            if value
        )
