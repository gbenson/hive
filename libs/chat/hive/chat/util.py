from typing import Optional

from cloudevents.abstract import CloudEvent

from hive.messaging import Channel, blocking_connection

from .message import ChatMessage


def publish(
        message: ChatMessage | CloudEvent,
        *,
        routing_key: str,
        channel: Optional[Channel] = None,
) -> None:
    if isinstance(message, ChatMessage):
        message = message.json()

    if channel:
        _publish(channel, routing_key, message)
        return

    with blocking_connection(connection_attempts=1) as conn:
        _publish(conn.channel(), routing_key, message)


def _publish(channel: Channel, routing_key: str, message: ChatMessage) -> None:
    channel.publish_event(
        message=message,
        routing_key=routing_key,
    )
