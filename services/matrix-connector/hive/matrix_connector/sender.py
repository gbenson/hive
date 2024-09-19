import json
import logging
import os
import shutil
import subprocess

from enum import Enum

from pika import BasicProperties
from pika.spec import Basic

from hive.messaging import Channel, blocking_connection
from hive.service import RestartMonitor, ServiceStatus

from .units import SECONDS, MINUTES

logger = logging.getLogger(__name__)
d = logger.debug

MessageFormat = Enum("MessageFormat", "TEXT HTML MARKDOWN CODE EMOJIZE")


class Sender:
    def __init__(self, command: str = "matrix-commander"):
        filename = os.path.realpath(command)
        if filename is None:
            command = shutil.which(command)
        self._command = command

    def on_message(
            self,
            channel: Channel,
            method: Basic.Deliver,
            properties: BasicProperties,
            body: bytes,
    ):
        delivery_tag = method.delivery_tag
        try:
            content_type = properties.content_type
            if content_type != "application/json":
                raise ValueError(content_type)

            payload = json.loads(body)

            #try?
            self.send_messages(
                *payload["messages"],
                _format=MessageFormat.__members__[
                    payload["format"].upper()],
            )

            channel.basic_ack(delivery_tag=delivery_tag)

        except Exception:
            channel.basic_nack(delivery_tag=delivery_tag)
            logger.exception("EXCEPTION")

    def send_messages(
            self,
            *messages,
            _format: MessageFormat = MessageFormat.TEXT,
            max_retries: int = 4,
            initial_timeout: float = 30 * SECONDS,
            max_timeout: float = 5 * MINUTES,
    ):
        if not messages:
            logger.warning("Nothing to send")
            return

        command = [self._command]
        if _format is not MessageFormat.TEXT:
            command.append(f"--{_format.name.lower()}")
        command.append("--message")
        command.extend(messages)
        d("Executing: %s", command)

        timeout = initial_timeout
        while True:
            try:
                subprocess.run(
                    command,
                    shell=False,
                    #capture_output=True,
                    timeout=timeout,
                    check=True,  # XXX for now... should:
                    #                              1. capture output
                    #                              2. fwd errors to rabbit
                    #                              3. then raise
                )
                break

            except subprocess.TimeoutExpired as e:
                if max_retries < 1:
                    raise
                logger.warning(
                    f"{e}, will retry up to {max_retries} more time(s)")
            max_retries -= 1
            timeout = min(max_timeout, timeout * 2)
            d("Timeout is now {timeout} seconds")


class ReportingRestartMonitor(RestartMonitor):
    @property
    def status_emoji(self):
        return {
            ServiceStatus.HEALTHY: "",
            ServiceStatus.DUBIOUS: ":white_question_mark:",
        }.get(self.status, ":fire:")

    def report(self, sender: Sender):
        messages = list(self.messages)
        if not messages:
            return
        prefix = self.status_emoji
        if prefix:
            messages = [f"{prefix} {msg}" for msg in self.messages]
        #try?
        sender.send_messages(*messages, _format=MessageFormat.EMOJIZE)
        #except?


def main():
    logging.basicConfig(level=logging.INFO)
    rsm = ReportingRestartMonitor()
    logger.info("Service status: %s", rsm.status.name)
    sender = Sender()
    rsm.report(sender)

    queue = "matrix.messages.outgoing"
    with blocking_connection() as conn:
        channel = conn.channel()
        channel.queue_declare(
            queue=queue,
            durable=True,  # Persist across broker restarts.
        )
        channel.basic_qos(prefetch_count=1)  # Receive one message at a time.
        channel.basic_consume(
            queue=queue,
            on_message_callback=sender.on_message,
        )
        channel.start_consuming()
