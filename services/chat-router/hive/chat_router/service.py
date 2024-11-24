import logging

from collections.abc import Iterable
from dataclasses import dataclass, field

from hive.chat import ChatMessage
from hive.common import SmallCircularBuffer
from hive.messaging import Channel, Message
from hive.service import HiveService

from .handler import Handler
from .loader import HandlerLoader

logger = logging.getLogger(__name__)


@dataclass
class Service(HiveService):
    handlers: Iterable[Handler] = field(default_factory=HandlerLoader)
    our_recently_sent_messages: SmallCircularBuffer = field(
        default_factory=lambda: SmallCircularBuffer(8, coerce=str),
    )

    def _on_channel_open(self, channel: Channel):
        channel.add_pre_publish_hook(self.on_publish_event)

    def on_publish_event(self, channel: Channel, **kwargs):
        if not (message := kwargs.get("message")):
            return
        if not (uuid := message.get("uuid")):
            return
        self.our_recently_sent_messages.add(uuid)

    def on_chat_message(self, channel: Channel, message: Message):
        message = ChatMessage.from_json(message.json())
        if message.uuid in self.our_recently_sent_messages:
            return

        for handler in self.handlers:
            try:
                if handler.handle(channel, message):
                    return
            except Exception:
                logger.exception("EXCEPTION processing %s", message)
        logger.warning("Unhandled %s", message)

    def run(self):
        with self.blocking_connection(
                on_channel_open=self._on_channel_open,
        ) as conn:
            channel = conn.channel()
            channel.consume_events(
                queue="chat.messages",
                on_message_callback=self.on_chat_message,
            )
            channel.start_consuming()
