import logging

from cloudevents.abstract import CloudEvent

from hive.chat import tell_user
from hive.messaging import Channel, Message
from hive.service import HiveService

from .ping import handle_ping
from .reading_list import handle_link

logger = logging.getLogger(__name__)


class Service(HiveService):
    def run(self) -> None:
        with self.blocking_connection() as conn:
            channel = conn.channel()
            channel.consume_events(
                queue="matrix.events",
                on_message_callback=self.on_matrix_event,
            )
            channel.start_consuming()

    def on_matrix_event(self, channel: Channel, message: Message) -> None:
        event = message.event()
        if event.type != "net.gbenson.hive.matrix_event":
            raise ValueError(event.type)
        match event.subject:
            case "m.room.message":
                self.on_room_message(channel, event)
            case _:
                raise NotImplementedError(event.subject)

    def on_room_message(self, channel: Channel, event: CloudEvent) -> None:
        if event.data["sender"].startswith("@hive"):
            return
        content = event.data["content"]
        msgtype = content["msgtype"]
        if msgtype != "m.text":
            tell_user(f"icr {msgtype} messages", channel=channel)
            return
        body = content["body"]
        if not body:
            raise ValueError(content)
        self.on_text(channel, event, body)

    def on_text(self, channel: Channel, event: CloudEvent, text: str) -> None:
        if handle_ping(channel, text):
            return
        if handle_link(channel, text, event):
            return
        tell_user("idk what that is", channel=channel)
