import logging

from dataclasses import dataclass

from hive.chat import ChatMessage, tell_user
from hive.common.units import HOUR
from hive.messaging import Channel, Message

from .connector import ConnectorService

logger = logging.getLogger(__name__)


@dataclass
class Transitioner(ConnectorService):
    id_correlation_lifetime: float = 1 * HOUR

    def run(self):
        with self.blocking_connection() as conn:
            channel = conn.channel()
            channel.consume_events(
                queue="matrix.events",
                on_message_callback=self.on_matrix_event,
            )
            channel.start_consuming()

    def on_matrix_event(self, channel: Channel, message: Message):
        """Re-publish incoming Matrix events as chat messages.
        """
        try:
            message = ChatMessage.from_matrix_event(message.event().data)
        except Exception:
            logger.exception("EXCEPTION")
            return

        tell_user(message, channel=channel)

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


main = Transitioner.main
