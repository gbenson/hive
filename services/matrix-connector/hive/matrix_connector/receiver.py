import json
import logging
import sys

from contextlib import contextmanager
from dataclasses import dataclass
from functools import cached_property
from typing import Literal, Sequence

from hive.chat import ChatMessage, tell_user
from hive.common.units import HOUR

from .connector import ConnectorService

logger = logging.getLogger(__name__)
d = logger.debug


@dataclass
class Receiver(ConnectorService):
    matrix_commander_args: Sequence[str] = (
        "--listen", "forever",
        "--download-media", "media",
        "--download-media-name", "eventid",
        "--output", "json-max",
    )
    id_correlation_lifetime: float = 1 * HOUR

    def __post_init__(self):
        super().__post_init__()
        self._channel = None
        self._print_output = None

    @cached_property
    def matrix_commander(self):
        d("Importing matrix_commander")
        assert "matrix_commander" not in sys.modules
        from matrix_commander import matrix_commander
        return matrix_commander

    @cached_property
    def obj_to_dict(self):
        return self.matrix_commander.obj_to_dict

    def run(self):
        d("Entering Receiver.run")
        argv = [sys.argv[0]] + list(self.matrix_commander_args)
        with self.publisher_connection() as conn:
            with self.patched_print_output(conn.channel()):
                d("Entering matrix_commander.main")
                return self.matrix_commander.main(argv)

    @contextmanager
    def patched_print_output(self, channel):
        mc = self.matrix_commander
        d("Patching print_output")
        assert self._print_output is None
        self._print_output = mc.print_output
        mc.print_output = self.on_matrix_commander_output
        try:
            d("print_output patched")
            self._channel = channel
            yield self
        finally:
            d("Unpatching print_output")
            mc.print_output = self._print_output
            logger.info("Closing producer and cleaning up")
            self._channel = None
            self._print_output = None

    def on_matrix_commander_output(
            self,
            option: Literal["text", "json", "json-max", "json-spec"],
            *,
            text: str,
            json_: dict = None,
            json_max: dict = None,
            json_spec: dict = None,
    ) -> None:
        """Called by matrix-commander to print output.
        """
        if text:
            self._print_output("text", text=text)
        if not json_max:
            return
        try:
            self.on_matrix_event(json_max)
        except Exception:
            logger.exception("EXCEPTION")

    def on_matrix_event(self, event: dict):
        """Called whenever an event is received.
        """
        serialized_event = json.dumps(
            event,
            default=self.obj_to_dict
        ).encode("utf-8")

        self._channel.publish(
            message=serialized_event,
            content_type="application/json",
            routing_key="matrix.events",
        )

        try:
            message = ChatMessage.from_matrix_event(event["source"])
        except Exception as e:
            raise ValueError(event) from e
        tell_user(message, channel=self._channel)

        message_id = str(message.uuid)
        event_id = message.matrix.event_id
        self._valkey.set(
            f"message:{message_id}:event_id",
            event_id,
            ex=self.id_correlation_lifetime,
        )
        self._valkey.set(
            f"event:{event_id}:message_id",
            message_id,
            ex=self.id_correlation_lifetime,
        )


main = Receiver.main
