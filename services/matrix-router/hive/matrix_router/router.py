import logging

from hive.messaging import Channel

from .event import MatrixEvent

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
        raise NotImplementedError(f"event.body={event.body!r}")
