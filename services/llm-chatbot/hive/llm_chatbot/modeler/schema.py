from pydantic import BaseModel, ConfigDict, Field

from ..database import ContextID, MessageID, StreamID


# Note that we validate MessageID and ContextID because we use them to
# construct keys, e.g. "ctx:7e1958f6-2b64-4eaf-85a9-cdbcd6e4d8f1:msgs".
# Everything else in :class:`Message` just gets stored in a hash to be
# validated by whatever consumes them.

class Message(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: MessageID = Field(alias="message_id")


class Action(BaseModel):
    """An entry in the journal stream.
    """
    model_config = ConfigDict(extra="allow")

    id: StreamID
    """This action's entry ID in the journal stream."""

    type: str = Field(alias="action")
    context_id: ContextID

    @property
    def message(self) -> Message:
        return Message.model_validate(self.model_extra)

    @property
    def monotonic_id(self) -> float:
        """A number higher than any previous action processed.

        Used as a sorted set score to order messages in contexts.
        """
        return float(self.id.replace("-", "."))
