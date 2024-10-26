import json

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional

from pika import BasicProperties
from pika.spec import Basic

from hive.messaging import Channel, blocking_connection

from .event import MatrixEvent


@dataclass
class Service(ABC):
    input_queue: str = "matrix.events.received"
    on_channel_open: Optional[Callable[[Channel], None]] = None

    @abstractmethod
    def on_matrix_event(
            self,
            channel: Channel,
            event: MatrixEvent,
    ):
        raise NotImplementedError

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
        event = MatrixEvent(json.loads(body))
        self.on_matrix_event(channel, event)

    def run(self):
        with blocking_connection(on_channel_open=self.on_channel_open) as conn:
            channel = conn.channel()
            channel.consume_events(
                queue=self.input_queue,
                on_message_callback=self._on_matrix_event,
                dead_letter=True,
            )
            channel.start_consuming()
