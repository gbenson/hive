import json

from dataclasses import dataclass

from pika import BasicProperties
from pika.spec import Basic

from hive.messaging import Channel
from hive.service import HiveService

from . import smoke_test_corpus
from .event import MatrixEvent
from .reaction_manager import reaction_manager
from .router import Router


@dataclass
class Service(Router, HiveService):
    input_queue: str = "matrix.events.received"
    event_queues: list[str] | tuple[str] = (
        "readinglist.updates",
    )

    def _on_matrix_event(
            self,
            channel: Channel,
            method: Basic.Deliver,
            properties: BasicProperties,
            body: bytes,
    ):
        content_type = properties.content_type
        if content_type != "application/json":
            raise ValueError(content_type)
        smoke_test_corpus.maybe_add_event(body)
        event = MatrixEvent(json.loads(body))
        self.on_matrix_event(channel, event)

    def run(self):
        with self.blocking_connection() as conn:
            channel = conn.channel()
            for queue in self.event_queues:
                channel.consume_events(
                    queue=queue,
                    on_message_callback=reaction_manager.on_event,
                )
            channel.consume_events(
                queue=self.input_queue,
                on_message_callback=self._on_matrix_event,
                mandatory=True,
            )
            channel.start_consuming()
