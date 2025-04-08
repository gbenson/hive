from cloudevents.abstract import CloudEvent

from hive.common.units import SECOND
from hive.messaging import Channel, Message
from hive.service import HiveService

from .ping import handle_ping
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
        if event.subject != "m.room.message":
            return
        try:
            self.on_room_message(channel, event)
        except NotImplementedError:
            channel.send_reaction("😕", in_reply_to=event)
            raise
        except Exception:
            channel.send_reaction("❌", in_reply_to=event)
            raise

    def on_room_message(self, channel: Channel, event: CloudEvent) -> None:
        request = Request(event)
        if request.sender.startswith("@hive"):
            return
        if request.is_reading_list_update_request:
            self.on_reading_list_update_request(channel, request)
            return

        if handle_ping(channel, request.text):
            return
        channel.tell_user("idk what that is")

    def on_reading_list_update_request(
            self,
            channel: Channel,
            request: Request,
    ) -> None:
        channel.set_user_typing(5 * SECOND)
        channel.publish_request(
            routing_key="readinglist.update.requests",
            time=request.time,
            data={
                "body": request.text,
                "content_type": "text/plain",
                "created_from": request.origin,
            },
        )
