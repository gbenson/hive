from dataclasses import dataclass
from functools import cached_property

from cloudevents.abstract import CloudEvent

from hive.chat.matrix import RoomMessageEvent


@dataclass
class Request:
    event: CloudEvent

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
