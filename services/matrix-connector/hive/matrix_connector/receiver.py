import json
import logging
import sys

from contextlib import contextmanager
from dataclasses import dataclass
from functools import cached_property
from typing import Iterable, Literal, Optional

from hive.common.functools import once
from hive.messaging import publisher_connection
from hive.service import RestartMonitor

logger = logging.getLogger(__name__)
d = logger.debug


@dataclass
class Receiver:
    queue_name: str = "matrix.events.received"

    def __post_init__(self):
        self._setup_logging()
        d("Initializing")

        self._restart_monitor = RestartMonitor()
        self._channel = None
        self._print_output = None

    @cached_property
    def log_level(self):
        if "--debug" in sys.argv[1:]:
            return logging.DEBUG
        return logging.INFO

    def _setup_logging(self):
        logger.setLevel(self.log_level)

    @cached_property
    def matrix_commander(self):
        d("Importing matrix_commander")
        assert "matrix_commander" not in sys.modules
        from matrix_commander import matrix_commander
        return matrix_commander

    @cached_property
    def obj_to_dict(self):
        return self.matrix_commander.obj_to_dict

    def __call__(self, argv: Optional[Iterable[str]] = None):
        d("Entering receiver.main")

        if not argv:
            argv = sys.argv
        if argv[1:] in [[], ["--debug"]]:
            argv = argv[:]
            argv.extend((
                "--listen", "forever",
                "--output", "json-max",
            ))

        on_channel_open = once(self._restart_monitor.report_via_channel)
        with publisher_connection(on_channel_open=on_channel_open) as conn:
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
            logger.exception("LOGGED EXCEPTION")

    def on_matrix_event(self, event: dict):
        """Called whenever an event is received.
        """
        serialized_event = json.dumps(
            event,
            default=self.obj_to_dict
        ).encode("utf-8")

        self._channel.publish_event(
            message=serialized_event,
            content_type="application/json",
            routing_key=self.queue_name,
            mandatory=True,
        )


main = Receiver()
