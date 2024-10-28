import json
import os

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property
from hashlib import sha256
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

    @cached_property
    def _corpus_dir(self):
        dirname = os.environ.get("HIVE_MATRIX_EVENT_CORPUS")
        if not dirname:
            return None
        gitignore = os.path.join(dirname, ".gitignore")
        if not os.path.exists(gitignore):
            return None
        return dirname

    def _maybe_write_to_corpus(self, body: bytes):
        dirname = self._corpus_dir
        if not dirname:
            return
        basename = sha256(body).hexdigest()
        filename = os.path.join(dirname, basename + ".json")
        with open(filename, "wb") as fp:
            fp.write(body)

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
        self._maybe_write_to_corpus(body)
        event = MatrixEvent(json.loads(body))
        self.on_matrix_event(channel, event)

    def run(self):
        with blocking_connection(on_channel_open=self.on_channel_open) as conn:
            channel = conn.channel()
            channel.consume_events(
                queue=self.input_queue,
                on_message_callback=self._on_matrix_event,
                mandatory=True,
            )
            channel.start_consuming()
