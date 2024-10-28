import json
import logging

from dataclasses import dataclass
from functools import cached_property
from math import ceil
from typing import Any, Callable, Optional
from urllib.parse import urlencode, urlparse, urlunparse

import requests

from pika import BasicProperties
from pika.spec import Basic

from valkey import Valkey

from hive.common.units import HOURS
from hive.messaging import Channel, blocking_connection

logger = logging.getLogger(__name__)
d = logger.info  # logger.debug


@dataclass
class Service:
    input_queue: str = "user.notification.requests"
    on_channel_open: Optional[Callable[[Channel], None]] = None
    dedup_window: float = 24*HOURS
    gotify_url: str = "http://gotify"
    valkey_url: str = "valkey://valkey"

    @cached_property
    def _valkey(self) -> Valkey:
        return Valkey.from_url(self.valkey_url)

    @property
    def _dedup_window(self) -> int:
        return int(ceil(self.dedup_window))

    def _push_url(self, app_token) -> str:
        scheme, netloc, path = urlparse(self.gotify_url)[:3]
        if not path.endswith("/"):
            path += "/"
        path += "message"
        query = urlencode({"token": app_token})
        return urlunparse((scheme, netloc, path, "", query, ""))

    def on_notification_request(
        self,
        channel: Channel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ):
        content_type = properties.content_type
        if content_type != "application/json":
            raise ValueError(content_type)
        body = json.loads(body)

        meta = body.pop("meta")
        uuid = meta["uuid"]

        dedup_key = f"notifications:{uuid}"
        if self._valkey.incr(dedup_key) > 1:
            d("%s: already sent", dedup_key)
            return  # already sent

        try:
            self._valkey.expire(dedup_key, self._dedup_window)
            response = self._send_notification(body)
        except Exception:
            try:
                self._valkey.decr(dedup_key)  # it wasn't sent
            except Exception:
                pass
            raise
        d("response: %s", response)

    def _send_notification(self, body: dict[str, Any]):
        app_token = body.pop("channel_id")
        d("request: %s", body)
        r = requests.post(self._push_url(app_token), json=body)
        r.raise_for_status()
        return r.json()

    def run(self):
        with blocking_connection(on_channel_open=self.on_channel_open) as conn:
            channel = conn.channel()
            channel.consume_requests(
                queue=self.input_queue,
                on_message_callback=self.on_notification_request,
            )
            channel.start_consuming()
