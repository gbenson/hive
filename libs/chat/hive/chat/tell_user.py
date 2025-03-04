from typing import Optional

from hive.messaging import Channel, blocking_connection

from .message import ChatMessage


def tell_user(
        text: str | ChatMessage,
        *,
        channel: Optional[Channel] = None,
        **kwargs
) -> ChatMessage:
    """Send a ChatMessage.
    """
    if isinstance(text, ChatMessage):
        if kwargs:
            raise ValueError
        message = text
    else:
        message = ChatMessage(text=text, **kwargs)

    if channel:
        return _tell_user(channel, message)

    with blocking_connection(connection_attempts=1) as conn:
        return _tell_user(conn.channel(), message)


def _tell_user(channel: Channel, message: ChatMessage) -> ChatMessage:
    channel.publish_event(
        message=message.json(),
        routing_key="chat.messages",
    )
    return message
