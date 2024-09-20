import asyncio
import json
import logging
import sys

from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from functools import cached_property
from typing import Iterable, Literal, Optional

from hive.common.units import GiB
from hive.messaging import producer_connection

logger = logging.getLogger(__name__)
d = logger.debug


@dataclass
class Receiver:
    stream_name: str = "matrix.events.received"
    stream_max_length_bytes: int = 8 * GiB

    def __post_init__(self):
        self._setup_logging()
        d("Initializing")

        self._producer = None
        self._async_main = None
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
                "--listen-self",
                "--output", "json-max",
            ))

        with self.patched_async_main():
            d("Entering matrix_commander.main")
            return self.matrix_commander.main(argv)

    @contextmanager
    def patched_async_main(self):
        mc = self.matrix_commander
        d("Patching async_main")
        assert self._async_main is None
        self._async_main = mc.async_main
        mc.async_main = self.async_main
        try:
            d("async_main patched")
            yield self
        finally:
            d("NOT unpatching async_main")

    async def async_main(self):
        self._setup_logging()
        d("Entered receiver.async_main")
        async with producer_connection() as producer:
            d("Connected to producer")
            await producer.create_stream(
                stream=self.stream_name,
                arguments={
                    "max-length-bytes": self.stream_max_length_bytes,
                },
                exists_ok=True,
            )
            d("Created stream")
            self._producer = producer
            async with self.patched_print_output():
                d("Entering matrix_commander.async_main")
                try:
                    await self._async_main()
                finally:
                    logger.info("Closing producer and cleaning up")

    @asynccontextmanager
    async def patched_print_output(self):
        mc = self.matrix_commander
        d("Patching print_output")
        assert self._print_output is None
        self._print_output = mc.print_output
        mc.print_output = self.on_matrix_commander_output
        try:
            d("print_output patched")
            yield self
        finally:
            d("NOT unpatching print_output")

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

        event_loop = asyncio.get_running_loop()
        coroutine = self._producer.send(
            stream=self.stream_name,
            message=serialized_event,
        )

        future = asyncio.run_coroutine_threadsafe(
            coroutine,
            event_loop,
        )

        return future.result


main = Receiver()
