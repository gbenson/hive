import json
import logging
import os
import subprocess

from dataclasses import dataclass
from enum import Enum
from shutil import which

from hive.chat import ChatMessage
from hive.common.units import SECONDS, MINUTES
from hive.messaging import Channel, Message

from .connector import ConnectorService

logger = logging.getLogger(__name__)
d = logger.info  # logger.debug

MessageFormat = Enum("MessageFormat", "TEXT HTML MARKDOWN CODE EMOJIZE")


@dataclass
class Sender(ConnectorService):
    command: str = "matrix-commander"

    def __post_init__(self):
        super().__post_init__()
        if not os.path.dirname(self.command):
            self.command = which(self.command)

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
        d("%s: Received", message.uuid)
        try:
            self._on_chat_message(channel, message)
        finally:
            d("%s: Processing complete", message.uuid)

    def _on_chat_message(self, channel: Channel, message: ChatMessage):
        if not self._should_forward(message):
            d("%s: Nothing to do", message.uuid)
            return

        kwargs = {"message_uuid": message.uuid}
        if (messages := message.html):
            kwargs["_format"] = MessageFormat.HTML
        else:
            messages = message.text
        self.send_messages(messages, **kwargs)

    def send_messages(
            self,
            *messages,
            _format: MessageFormat = MessageFormat.TEXT,
            max_retries: int = 4,
            initial_timeout: float = 30 * SECONDS,
            max_timeout: float = 5 * MINUTES,
            message_uuid: str = "[no-uuid]",
    ):
        if not messages:
            logger.warning("Nothing to send")
            return

        command = [self.command]
        if _format is not MessageFormat.TEXT:
            command.append(f"--{_format.name.lower()}")
        command.append("--message")
        command.extend(messages)

        timeout = initial_timeout
        while True:
            d("%s: Executing: %s", message_uuid, command)
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

    def on_reading_list_update(self, channel: Channel, message: Message):
        event = message.json()
        origin = event.get("meta", {}).get("origin", {})
        if origin.get("channel") != "chat":
            return
        message = ChatMessage.from_json(origin["message"])
        d("%s: Received", message.uuid)
        event = message.matrix
        if not event:
            d("%s: Nothing to do", message.uuid)
            return
        try:
            self.send_reaction("👍", event.event_id, message_uuid=message.uuid)
        finally:
            d("%s: Processing complete", message.uuid)

    def send_reaction(
            self,
            reaction: str,
            receiving_event_id: str,
            max_retries: int = 4,
            initial_timeout: float = 30 * SECONDS,
            max_timeout: float = 5 * MINUTES,
            message_uuid: str = "[no-uuid]",
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

        command = [self.command, "--event", "-"]

        timeout = initial_timeout
        while True:
            d("%s: Executing: %s", message_uuid, command)
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
                channel.consume_events(
                    queue="readinglist.updates",
                    on_message_callback=self.on_reading_list_update,
                )
            finally:
                if self.on_channel_open:
                    # deferred so we receive our own restart monitor message
                    self.on_channel_open(channel)
            channel.start_consuming()


main = Sender.main
