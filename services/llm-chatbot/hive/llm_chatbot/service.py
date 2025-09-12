import logging
import re

from dataclasses import dataclass

from cloudevents.abstract import CloudEvent

from hive.messaging import Channel, Message
from hive.service import HiveService

logger = logging.getLogger(__name__)
d = logger.info

REQUEST_TYPE_RE = re.compile(r"net.gbenson.hive.llm_chatbot_(\w+)_request")


@dataclass
class Service(HiveService):
    def run(self):
        with self.blocking_connection() as conn:
            channel = conn.channel()
            channel.consume_events(
                queue="llm.chatbot.requests",
                on_message_callback=self.on_request,
            )
            channel.start_consuming()

    def on_request(self, channel: Channel, message: Message):
        event = message.event()
        d("Received: %s", message.body.decode("utf-8"))  # XXX
        if not (match := REQUEST_TYPE_RE.fullmatch(event.type)):
            raise ValueError(event.type)
        request_type = match.group(1)
        handler_name = f"on_{request_type}_request"
        if not (do := getattr(self, handler_name, None)):
            raise NotImplementedError(request_type)
        do(channel, event)

    def on_generate_response_request(
            self,
            channel: Channel,
            event: CloudEvent,
    ) -> None:
        channel.send_text("idk what that is", sender="hive")
