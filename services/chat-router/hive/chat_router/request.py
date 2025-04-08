from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from typing import Any
from urllib.parse import urlparse

from cloudevents.abstract import CloudEvent

from hive.chat.matrix import RoomMessageEvent


@dataclass
class Request:
    event: CloudEvent

    @property
    def origin(self) -> dict[str, Any]:
        """A summary of the initiating event, for correlation etc.
        """
        return {
            "id": self.event.id,
            "source": self.event.source,
            "type": self.event.type,
        }

    @cached_property
    def message(self) -> RoomMessageEvent:
        """Matrix "m.room.message".
        """
        return RoomMessageEvent.model_validate(self.event.data)

    @property
    def sender(self) -> str:
        """The fully-qualified Matrix ID of the initiating user.
        """
        return self.message.sender

    @property
    def time(self) -> datetime:
        """The timestamp on the originating Matrix homeserver
        when the Matrix event initiating this request was sent.
        """
        return self.message.time

    @cached_property
    def text(self) -> str:
        """The unparsed user input of this request.
        """
        content = self.message.content
        if (msgtype := content.msgtype) != "m.text":
            raise NotImplementedError(msgtype)
        if not (result := content.body.strip()):
            raise ValueError
        return result

    @cached_property
    def is_reading_list_update_request(self) -> bool:
        """Is this a reading list update request?
        """
        try:
            url = urlparse(self.text.split(maxsplit=1)[0])
        except Exception:
            return False
        return url.scheme in {"http", "https"}
