import re

from dataclasses import dataclass
from datetime import timedelta
from functools import cached_property
from html import escape
from typing import Optional

from valkey import Valkey

from hive.chat import tell_user
from hive.common import parse_datetime, parse_uuid
from hive.messaging import Channel, Message
from hive.service import HiveService, RestartMonitor


@dataclass
class Service(HiveService):
    service_status_event_queue: str = "service.status"
    valkey_url: str = "valkey://service-monitor-valkey"
    service_condition_window: timedelta = RestartMonitor.rapid_restart_cutoff

    @cached_property
    def _valkey(self) -> Valkey:
        return Valkey.from_url(self.valkey_url)

    def on_service_status_event(
            self,
            channel: Channel,
            message: Message,
    ):
        report = message.json()

        if report.get("meta", {}).get("type") == "service_status_report":
            uuid = parse_uuid(report["meta"]["uuid"])
            timestamp = parse_datetime(report["meta"]["timestamp"])
            service = report["service"]
            condition = report["condition"]
            messages = report.get("messages")

        elif report.get("type") == "net.gbenson.hive.service_status_report":
            uuid = parse_uuid(report["id"])
            timestamp = parse_datetime(report["time"])
            service = report["source"].rsplit("/", 1)[-1]
            condition = report["data"]["condition"].upper()
            messages = report["data"].get("messages")

        else:
            raise ValueError(message.body)

        if self._valkey.set(
                f"service:{service}:{condition}",
                message.body,
                ex=self.service_condition_window,
                get=True,
        ):
            return  # old news

        if not messages:
            messages = [f"Service became {condition}"]

        service_shortname = re.sub(r"^hive-", "", service, 1)
        messages = [
            re.sub(r"^Service\b", service_shortname, message, 1)
            for message in messages
        ]

        text = "\n".join(messages)
        try:
            html = "<br>".join(map(escape, messages))
            if html == text:
                html = None
        except Exception:
            html = None

        tell_user(
            channel=channel,
            text=text,
            html=self._to_html(text),
            timestamp=timestamp,
            uuid=uuid,
        )

    @staticmethod
    def _to_html(text: str) -> Optional[str]:
        lines = [line for line in text.split("\n") if line]
        if len(lines) <= 1:
            return None
        return "<br>".join(map(escape, lines))

    def run(self):
        with self.blocking_connection(on_channel_open=None) as conn:
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
