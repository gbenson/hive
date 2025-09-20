import logging

from dataclasses import dataclass, field
from datetime import date
from functools import partial
from pathlib import Path
from typing import ClassVar
from uuid import uuid4

from hive.common import ArgumentParser
from hive.messaging import Channel, Message
from hive.service import HiveService

logger = logging.getLogger(__name__)
d = logger.debug


@dataclass
class Service(HiveService):
    queues: list[str] = field(default_factory=list)
    topdir: Path = field(default_factory=Path.cwd)

    def make_argument_parser(self) -> ArgumentParser:
        parser = super().make_argument_parser()
        parser.add_argument(
            "queues",
            metavar="queue",
            nargs="+",
            help="queues to serialize",
        )
        return parser

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.queues:
            self.queues.extend(self.args.queues)
        if not self.queues:
            raise ValueError

    def run(self) -> None:
        with self.blocking_connection() as conn:
            channel = conn.channel()
            for queue in self.queues:
                channel.consume_events(
                    queue=queue,
                    on_message_callback=partial(self.on_message, queue),
                )
            logger.info("Consuming %s", ", ".join(self.queues))
            channel.start_consuming()

    EXTENSIONS: ClassVar[dict[str, str]] = {
        "application/cloudevents+json": ".json",
        "application/json": ".json",
        "message/rfc822": ".eml",
    }

    def on_message(
            self,
            queue: str,
            channel: Channel,
            message: Message,
    ) -> None:
        dirpath = self.topdir / queue / date.today().strftime("%Y%m%d")
        extension = self.EXTENSIONS.get(message.content_type or "", "")
        path = dirpath / f"{uuid4()}{extension}"
        dirpath.mkdir(parents=True, exist_ok=True)
        bytes_written = path.write_bytes(message.body)

        # Be very careful not to log anything here that might loop
        # if this service is configured to consume events that are
        # emitted as a result of these log messages being scraped!
        d("Wrote %s (%d bytes)", path, bytes_written)
