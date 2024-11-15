import json
import re

from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from typing import Callable, Optional
from uuid import RFC_4122, UUID

from pika import BasicProperties
from pika.spec import Basic

from valkey import Valkey

from hive.common.units import MINUTES
from hive.messaging import Channel, blocking_connection


@dataclass
class Service:
    service_status_event_queue: str = "service.status"
    valkey_url: str = "valkey://service-monitor-valkey"
    service_condition_window: float = 5 * MINUTES
    on_channel_open: Optional[Callable[[Channel], None]] = None

    @cached_property
    def _valkey(self) -> Valkey:
        return Valkey.from_url(self.valkey_url)

    def on_service_status_event(
        self,
        channel: Channel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ):
        content_type = properties.content_type
        if content_type != "application/json":
            raise ValueError(content_type)
        report = json.loads(body)

        if report["meta"]["type"] != "service_status_report":
            raise ValueError(body)

        uuid = UUID(report["meta"]["uuid"])
        if uuid.variant != RFC_4122:
            raise ValueError(body)
        if uuid.version != 4:
            raise ValueError(body)

        timestamp = datetime.fromisoformat(report["meta"]["timestamp"])

        service = report["service"]
        condition = report["condition"]

        if self._valkey.set(
                f"service:{service}:{condition}",
                body,
                ex=self.service_condition_window,
                get=True,
        ):
            return  # old news

        messages = report.get("messages")
        if not messages:
            messages = [f"{service} became {condition}"]

        messages = [
            re.sub(r"^Service\b", service, message, 1)
            for message in messages
        ]

        channel.tell_user(
            "\n".join(messages),
            timestamp=timestamp,
            uuid=uuid,
        )

    def run(self):
        with blocking_connection() as conn:
            channel = conn.channel()
            try:
                channel.consume_events(
                    queue=self.service_status_event_queue,
                    on_message_callback=self.on_service_status_event,
                )
            finally:
                if self.on_channel_open:
                    # deferred so we receive our own events
                    self.on_channel_open(channel)
            channel.start_consuming()
