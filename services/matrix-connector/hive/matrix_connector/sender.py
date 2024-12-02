import json
import logging
import os
import subprocess

from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from shutil import which

from valkey import Valkey

from hive.chat import ChatMessage
from hive.common.units import SECONDS, MINUTES
from hive.messaging import Channel, Message
from hive.service import HiveService

logger = logging.getLogger(__name__)
d = logger.debug

MessageFormat = Enum("MessageFormat", "TEXT HTML MARKDOWN CODE EMOJIZE")


@dataclass
class Sender(HiveService):
    command: str = "matrix-commander"
    valkey_url: str = "valkey://matrix-valkey"

    def __post_init__(self):
        super().__post_init__()
        if not os.path.dirname(self.command):
            self.command = which(self.command)

    @cached_property
    def _valkey(self) -> Valkey:
        return Valkey.from_url(self.valkey_url)

    def _should_forward(self, message: ChatMessage) -> bool:
        if message.sender != "hive":
            return False
        orig_message_id = message.in_reply_to
        if not orig_message_id:
            return True
        event_id = self._valkey.get(f"message:{orig_message_id}:event_id")
        return bool(event_id)

    def on_chat_message(self, channel: Channel, message: Message):
        message = ChatMessage.from_json(message.json())
        if not self._should_forward(message):
            return
        if message.html:
            self.send_messages(message.html, "html")
        else:
            self.send_messages(message.text)

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

        command = [self.command]
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

    def run(self):
        with self.blocking_connection(on_channel_open=None) as conn:
            channel = conn.channel()
            try:
                channel.consume_events(
                    queue="chat.messages",
                    on_message_callback=self.on_chat_message,
                )
            finally:
                if self.on_channel_open:
                    # deferred so we receive our own restart monitor message
                    self.on_channel_open(channel)
            channel.start_consuming()


main = Sender.main
