import json
import logging
import zlib

from argparse import ArgumentParser
from dataclasses import dataclass
from socket import gethostname
from typing import Optional

from pika import BasicProperties
from pika.spec import Basic

from hive.messaging import blocking_connection

from ..channel import Channel

logger = logging.getLogger(__name__)


def main():
    parser = ArgumentParser(
        description="Churn messages from one queue to another.",
    )
    parser.add_argument(
        "source_queue", metavar="SOURCE",
        help="queue to consume from")
    parser.add_argument(
        "target_queue", metavar="TARGET", nargs="?",
        help="queue to publish to")
    parser.add_argument(
        "-v", "--verbose", action="count", default=0,
        help="increase verbosity (up to -vvv)")
    args = parser.parse_args()

    if (verbosity := args.verbose):
        logging.basicConfig(level={
            1: logging.WARNING,
            2: logging.INFO,
        }.get(verbosity, logging.DEBUG))

    worker = Worker(args.source_queue, args.target_queue)
    worker.run()


@dataclass
class Worker:
    source_queue: str
    target_queue: Optional[str] = None
    hostname: str = gethostname()
    mime_type: str = "application/vnd.gbenson.hive-messaging-smoke-test"

    @property
    def queues(self):
        yield self.source_queue
        if self.target_queue:
            yield self.target_queue

    def run(self):
        with blocking_connection() as conn:
            channel = conn.channel()
            self._run(channel)

    def _run(self, channel: Channel):
        for queue in self.queues:
            channel.queue_declare(
                queue=queue,
                durable=True,  # Persist across broker restarts.
            )
        channel.basic_qos(prefetch_count=1)  # Receive one message at a time.
        channel.basic_consume(
            queue=self.source_queue,
            on_message_callback=self._on_message,
        )
        channel.start_consuming()

    def _on_message(
            self,
            channel: Channel,
            method: Basic.Deliver,
            properties: BasicProperties,
            body: bytes,
    ):
        delivery_tag = method.delivery_tag
        try:
            content_type = properties.content_type
            if content_type == "application/json":
                exchange = method.exchange
                if exchange != "":
                    raise ValueError(exchange)

                routing_key = method.routing_key
                if routing_key != self.source_queue:
                    raise ValueError(routing_key)

                if not self.target_queue:
                    raise ValueError

                self._churn_forward(channel, body)

            elif content_type == self.mime_type:
                if self.target_queue:
                    raise ValueError(self.target_queue)

                self._churn_reversed(channel, body)

            else:
                raise ValueError(content_type)

            channel.basic_ack(delivery_tag=delivery_tag)

        except Exception:
            channel.basic_nack(delivery_tag=delivery_tag)
            logger.exception("EXCEPTION")
            raise  # XXX

    def _churn_forward(self, channel: Channel, body: bytes):
        msg = json.loads(body)

        if "routing_key" in msg:
            raise ValueError(msg["routing_key"])
        msg["routing_key"] = self.source_queue

        if "smoke_counts" not in msg:
            msg["smoke_counts"] = {}
        counts = msg["smoke_counts"]
        counts[self.hostname] = counts.get(self.hostname, 0) + 1

        body = zlib.compress(json.dumps(msg).encode("utf-8"))
        channel.send_to_queue(self.target_queue, body, self.mime_type)

    def _churn_reversed(self, channel: Channel, body: bytes):
        msg = json.loads(zlib.decompress(body))
        target_queue = msg.pop("routing_key")
        counts = msg["smoke_counts"]
        counts[self.hostname] = counts.get(self.hostname, 0) + 1
        channel.send_to_queue(target_queue, msg)
