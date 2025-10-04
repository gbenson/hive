import logging

from dataclasses import dataclass
from datetime import timedelta
from io import StringIO

from hive.common import dynamic_cast, utc_now
from hive.common.units import SECOND
from hive.messaging import Channel, Message
from hive.service import HiveService

from .response_manager import ResponseManager
from .schema import Request

logger = logging.getLogger(__name__)
d = logger.info


@dataclass
class Service(HiveService):
    """The controller service handles "ollama" commands.
    """
    max_request_age: timedelta = 30 * SECOND

    def run(self) -> None:
        with self.blocking_connection() as conn:
            channel = conn.channel()
            channel.consume_events(
                queue="llm.chatbot.ollama.commands",
                on_message_callback=self.on_message,
            )
            channel.start_consuming()

    def on_message(self, channel: Channel, message: Message) -> None:
        event = message.event()
        d("Received: %s", message.body.decode("utf-8"))

        request = Request.from_cloudevent(event)

        deadline = request.time + self.max_request_age
        if deadline < utc_now():
            d("%s: command deadline expired", event.id)
            return

        app = ResponseManager(channel, request, out=StringIO())
        try:
            app.run()
        except Exception:
            logger.exception("EXCEPTION")
            app.out.write("\n🤮")

        if (output := dynamic_cast(StringIO, app.out).getvalue().strip()):
            channel.send_text(html=output)
            channel.set_user_typing(False)
