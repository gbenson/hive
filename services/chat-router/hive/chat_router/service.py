import logging

from dataclasses import dataclass, field
from functools import cache

from cloudevents.abstract import CloudEvent

from hive.common.units import SECOND
from hive.messaging import Channel, Message
from hive.service import HiveService

from .brain import router
from .config import Config
from .llm import LLM
from .request import Request

logger = logging.getLogger(__name__)
d = logger.info


@dataclass
class Service(HiveService):
    config: Config = field(default_factory=Config.read)
    llm: LLM = field(default_factory=LLM)

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

        sender = self.config.lookup_user(matrix_id=request.sender)
        if not sender:
            self.on_unknown_sender(request.sender)
            return
        role = sender.role

        self.llm.update_context(channel, request, role=role)

        if role == "user" and request.is_reading_list_update_request:
            # Note that reading-list-updater will send extra
            # LLM context updates to add detail to this one.
            self.on_reading_list_update_request(channel, request)
            return

        if role != "user":
            return

        router.dispatch(request, self, channel)

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

    def on_send_text(self, channel: Channel, text: str) -> None:
        channel.send_text(text)

    @staticmethod
    @cache
    def on_unknown_sender(matrix_id: str) -> None:
        logger.warning("Ignoring event from unknown sender %s", matrix_id)
