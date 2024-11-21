import logging

from uuid import uuid4

from hive.messaging import Channel

from .event import MatrixEvent
from .ping_pong import response_for_challenge, route_response_for_challenge
from .reading_list import is_reading_list_update, route_reading_list_update

logger = logging.getLogger(__name__)
d = logger.info  # logger.debug


class Router:
    def on_matrix_event(self, channel: Channel, event: MatrixEvent):
        match event.event_type:
            case "m.room.message":
                self._on_room_message(channel, event)
            case unhandled_type:
                raise NotImplementedError(unhandled_type)

    def _on_room_message(self, channel: Channel, event: MatrixEvent):
        match event.content.msgtype:
            case "m.text":
                self._on_text_message(channel, event)
            case "m.image":
                self._on_image(channel, event)
            case unhandled_type:
                raise NotImplementedError(unhandled_type)

    def _on_text_message(self, channel: Channel, event: MatrixEvent):
        chatmsg = {
                "text": event.body,
                "html": event.html,
                "sender": (
                    "hive" if event.sender.startswith("@hive")
                    else "user"
                ),
                "timestamp": str(event.timestamp),
                "uuid": str(uuid4()),
                "matrix": {
                    "event_id": event.event_id,
                },
            }
        chatmsg = dict((key, value) for key, value in chatmsg.items() if value)
        d("SENDING: %r", chatmsg)
        channel.publish_event(
            message=chatmsg,
            routing_key="chat.messages",
        )

        if (response := response_for_challenge(event.body)):
            route_response_for_challenge(channel, response)
            return
        if is_reading_list_update(event):
            route_reading_list_update(channel, event)
            return
        raise NotImplementedError(f"event.body={event.body!r}")
