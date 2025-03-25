import re

from dataclasses import dataclass
from datetime import timedelta
from functools import cached_property
from html import escape
from typing import Optional

from cloudevents.pydantic import CloudEvent
from valkey import Valkey

from hive.chat import tell_user
from hive.common import parse_datetime, parse_uuid
from hive.messaging import Channel, Message
from hive.service import HiveService, RestartMonitor


@dataclass
class Service(HiveService):
    service_status_report_queue: str = "service.status.reports"
    valkey_url: str = "valkey://service-monitor-valkey"
    service_condition_window: timedelta = RestartMonitor.rapid_restart_cutoff

    @cached_property
    def _valkey(self) -> Valkey:
        return Valkey.from_url(self.valkey_url)

    def on_service_status_report(self, channel: Channel, message: Message):
        """Handle a new-style CloudEvent status report.
        """
        self._on_service_status_report(channel, message, message.event())

    def on_service_status_event(self, channel: Channel, message: Message):
        """Handle an old-style (non-CloudEvent) report.
        """
        data = message.json()
        meta = data.pop("meta")
        service = data.pop("service")
        data["condition"] = data["condition"].lower()

        event = CloudEvent(
            id=meta["uuid"],
            source=f"https://gbenson.net/hive/services/{service}",
            type="net.gbenson.hive.service_status_report",
            time=parse_datetime(meta["timestamp"]),
            subject=service,
            data=data,
        )

        self._on_service_status_report(channel, message, event)

    def _on_service_status_report(
            self,
            channel: Channel,
            message: Message,
            report: CloudEvent,
    ):
        """Handle a new-style CloudEvent status report.
        """
        uuid = parse_uuid(report.id)
        timestamp = report.time
        service = report.subject
        condition = report.data["condition"].upper()

        if self._valkey.set(
                f"service:{service}:{condition}",
                message.body,
                ex=self.service_condition_window,
                get=True,
        ):
            return  # old news

        messages = report.data.get("messages")
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
                    queue=self.service_status_report_queue,
                    on_message_callback=self.on_service_status_report,
                )
            finally:
                if self.on_channel_open:
                    # deferred so we receive our own events
                    self.on_channel_open(channel)
            channel.start_consuming()
