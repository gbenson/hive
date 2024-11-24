import json
import logging
import os
import re
import shutil
import subprocess

from enum import Enum

from pika import BasicProperties
from pika.spec import Basic

from hive.common import ArgumentParser
from hive.common.units import SECONDS, MINUTES
from hive.messaging import Channel, blocking_connection
from hive.service import RestartMonitor, ServiceCondition

logger = logging.getLogger(__name__)
d = logger.debug

MessageFormat = Enum("MessageFormat", "TEXT HTML MARKDOWN CODE EMOJIZE")

DEFAULT_INPUT_QUEUE = "test.matrix.message.send.requests"


class Sender:
    def __init__(self, command: str = "matrix-commander"):
        filename = os.path.realpath(command)
        if filename is None:
            command = shutil.which(command)
        self._command = command

    def on_send_message_request(
            self,
            channel: Channel,
            method: Basic.Deliver,
            properties: BasicProperties,
            body: bytes,
    ):
        content_type = properties.content_type
        if content_type != "application/json":
            raise ValueError(content_type)

        payload = json.loads(body)

        self.send_messages(
            *payload["messages"],
            _format=MessageFormat.__members__[
                payload["format"].upper()],
        )

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

    def on_send_reaction_request(
            self,
            channel: Channel,
            method: Basic.Deliver,
            properties: BasicProperties,
            body: bytes,
    ):
        content_type = properties.content_type
        if content_type != "application/json":
            raise ValueError(content_type)

        payload = json.loads(body)
        self.send_reaction(
            reaction=payload["reaction"],
            receiving_event_id=payload["receiver"]["event_id"],
        )

    def send_reaction(
            self,
            reaction: str,
            receiving_event_id: str,
            max_retries: int = 4,
            initial_timeout: float = 30 * SECONDS,
            max_timeout: float = 5 * MINUTES,
    ):
        event = json.dumps({
            "type": "m.reaction",
            "content": {
                "m.relates_to": {
                    "event_id": receiving_event_id,
                    "key": reaction,
                    "rel_type": "m.annotation",
                },
            },
        }).encode("utf-8")

        command = [self._command, "--event", "-"]
        d("Executing: %s", command)

        timeout = initial_timeout
        while True:
            try:
                subprocess.run(
                    command,
                    shell=False,
                    input=event,
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
            ServiceCondition.HEALTHY: "",
            ServiceCondition.DUBIOUS: ":white_question_mark:",
        }.get(self.status.condition, ":fire:")

    def report(self, sender: Sender):
        if self.multiple_restarts_logged:
            return
        messages = self.status.messages
        if not messages:
            return
        replacer = re.compile(r"^Service\b")
        messages = [replacer.sub(self.name, msg) for msg in messages]
        prefix = self.status_emoji
        if prefix:
            messages = [f"{prefix} {msg}" for msg in messages]
        #try?
        sender.send_messages(*messages, _format=MessageFormat.EMOJIZE)
        #except?


def main():
    parser = ArgumentParser(
        description="Publish messages to Hive's Matrix room.",
    )
    parser.add_argument(
        "--consume", dest="queue", default=DEFAULT_INPUT_QUEUE,
        help=f"queue to consume [default: {DEFAULT_INPUT_QUEUE}]",
    )
    args = parser.parse_args()

    rsm = ReportingRestartMonitor()
    sender = Sender()
    rsm.report(sender)

    message_queue = args.queue
    reaction_queue = message_queue.replace("message", "reaction")
    assert reaction_queue != message_queue

    with blocking_connection() as conn:
        channel = conn.channel()
        rsm.report_via_channel(channel)

        channel.consume_requests(
            queue=message_queue,
            on_message_callback=sender.on_send_message_request,
        )
        channel.consume_requests(
            queue=reaction_queue,
            on_message_callback=sender.on_send_reaction_request,
        )

        channel.start_consuming()
