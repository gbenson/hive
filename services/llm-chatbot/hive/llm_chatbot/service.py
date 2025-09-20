import logging
import re

from dataclasses import dataclass, field
from inspect import get_annotations

from hive.messaging import Channel, Message
from hive.service import HiveService

from .database import Database
from .schema import (
    BaseRequest,
    GenerateResponseRequest,
    UpdateContextRequest,
)

logger = logging.getLogger(__name__)
d = logger.info

REQUEST_KIND_RE = re.compile(r"net.gbenson.hive.llm_chatbot_(\w+)_request")


@dataclass
class Service(HiveService):
    database: Database = field(default_factory=Database)

    def run(self) -> None:
        with self.blocking_connection() as conn:
            channel = conn.channel()
            channel.consume_events(
                queue="llm.chatbot.requests",
                on_message_callback=self.on_request,
            )
            channel.start_consuming()

    def on_request(self, channel: Channel, message: Message) -> None:
        event = message.event()
        d("Received: %s", message.body.decode("utf-8"))

        # Get the request handler.
        if not (match := REQUEST_KIND_RE.fullmatch(event.type)):
            raise ValueError(event.type)
        request_kind = match.group(1)
        if not (handle_request := getattr(self, f"on_{request_kind}", None)):
            raise NotImplementedError(request_kind)

        # Get the request class.
        handler_annotations = get_annotations(handle_request)
        request_class_candidates = [
            param_type
            for param_name, param_type in handler_annotations.items()
            if issubclass(param_type, BaseRequest)
        ]
        if len(request_class_candidates) != 1:
            raise TypeError(handler_annotations)
        request_class = request_class_candidates[0]

        # Validate and handle the request.
        handle_request(channel, request_class.from_cloudevent(event))

    def on_update_context(
            self,
            channel: Channel,
            request: UpdateContextRequest,
    ) -> None:
        self.database.update_context(request.context_id, request.message)

    def on_generate_response(
            self,
            channel: Channel,
            request: GenerateResponseRequest,
    ) -> None:
        # XXX check the timestamp before hitting the LLM!
        # XXX then send a user_typing
        # model_input = self.database.get_messages(request.context_id)
        # d("Responding to: %s", model_input)
        channel.send_text("idk what that is", sender="hive")
