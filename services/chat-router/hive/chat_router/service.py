from cloudevents.abstract import CloudEvent

from hive.messaging import Channel, Message
from hive.service import HiveService

from .ping import handle_ping
from .reading_list import startswith_link, request_reading_list_update
from .request import Request


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
        try:
            self._on_room_message(channel, event)
        except NotImplementedError:
            channel.send_reaction("😕", in_reply_to=event)
            raise
        except Exception:
            channel.send_reaction("❌", in_reply_to=event)
            raise

    def _on_room_message(self, channel: Channel, event: CloudEvent) -> None:
        request = Request(event)
        if request.sender.startswith("@hive"):
            return

        user_input = request.text
        if startswith_link(user_input):
            request_reading_list_update(channel, event, user_input)
            return

        if handle_ping(channel, user_input):
            return
        channel.tell_user("idk what that is")
