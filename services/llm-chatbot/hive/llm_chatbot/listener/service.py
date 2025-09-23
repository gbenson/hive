import logging
import re

from inspect import get_annotations

from hive.messaging import Channel, Message

from ..service import BaseService
from .schema import (
    BaseRequest,
    GenerateResponseRequest,
    UpdateContextRequest,
)

logger = logging.getLogger(__name__)
d = logger.info

REQUEST_KIND_RE = re.compile(r"net.gbenson.hive.llm_chatbot_(\w+)_request")


class Service(BaseService):
    """The listener service marshals incoming requests into the database.
    """

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
        self.db.xadd(self.streams.journal, request.as_key_value_pairs())

    def on_generate_response(
            self,
            channel: Channel,
            request: GenerateResponseRequest,
    ) -> None:
        self.db.xadd(self.streams.requests, request.as_key_value_pairs())
