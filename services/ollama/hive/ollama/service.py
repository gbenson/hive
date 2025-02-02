import json
import logging

from collections.abc import Iterable
from dataclasses import dataclass
from functools import partial
from typing import Any, Callable, ClassVar, Optional, TypeAlias
from urllib.parse import urlparse, urljoin

import requests

from hive.common import ArgumentParser
from hive.messaging import Channel, Message
from hive.service import HiveService

logger = logging.getLogger(__name__)
d = logger.info


@dataclass
class Service(HiveService):
    DEFAULT_API_URL: ClassVar[str] = "http://ollama:11434"
    ollama_api_url: Optional[str] = None

    DEFAULT_QUEUE: ClassVar[str] = "ollama.api.requests"
    request_queue: Optional[str] = None

    def make_argument_parser(self) -> ArgumentParser:
        parser = super().make_argument_parser()
        parser.add_argument(
            "--ollama-api-url",
            metavar="URL",
            default=self.DEFAULT_API_URL,
            help=(f"URL to proxy requests to"
                  f" [default: {self.DEFAULT_API_URL}]"),
        )
        parser.add_argument(
            "--request-queue",
            metavar="QUEUE",
            default=self.DEFAULT_QUEUE,
            help=(f"Queue to consume requests from"
                  f" [default: {self.DEFAULT_QUEUE}]"),
        )
        parser.add_argument(
            "--request-queue-prefix",
            metavar="PREFIX",
            help=("Prefix to prepend to request queue name"
                  " [default: no prefix]"),
        )
        return parser

    def __post_init__(self):
        super().__post_init__()
        if not self.ollama_api_url:
            self.ollama_api_url = self.args.ollama_api_url
        if not self.request_queue:
            self.request_queue = self.args.request_queue
        if (prefix := self.args.request_queue_prefix):
            self.request_queue = f"{prefix}{self.request_queue}"

    def run(self):
        with self.blocking_connection() as conn:
            channel = conn.channel()
            channel.consume_rpc_requests(
                queue=self.request_queue,
                on_message_callback=self.on_request,
            )
            channel.start_consuming()

    def on_request(self, channel: Channel, message: Message):
        correlation_id = message.correlation_id
        try:
            response = self._on_request(channel, message)
            d("%s: response: %s", correlation_id, response)
            return response
        except Exception:
            logger.exception("%s: EXCEPTION", correlation_id)
            raise

    def _on_request(self, channel: Channel, message: Message):
        correlation_id = message.correlation_id
        request = message.json()
        d("%s: request: %s", correlation_id, request)

        base_url = self.ollama_api_url
        if not urlparse(base_url).path:
            base_url += "/"

        url = urljoin(base_url, request["request_uri"])
        if not url.startswith(base_url):
            raise ValueError(url)

        kwargs = {
            "timeout": (5, 25),
            "stream": True,
        }
        match (method := request["method"]):
            case "GET":
                pass
            case "POST":
                kwargs.update({"json": request["data"]})
            case _:
                raise NotImplementedError(method)

        r = requests.request(method, url, **kwargs)
        if r.status_code != 200:
            try:
                return r.json()
            except Exception:
                logger.exception("%s: EXCEPTION", correlation_id)
                return r.text

        return self.stream_response(
            messages=map(json.loads, r.iter_lines()),
            publish_message=partial(
                channel._publish_direct,
                routing_key=message.reply_to,
                exchange="",
                correlation_id=message.correlation_id,
            ),
        )

    _Message: ClassVar[TypeAlias] = dict[str, Any]
    _SENTINEL: ClassVar[_Message] = {}

    @classmethod
    def stream_response(
            cls,
            messages: Iterable[_Message],
            publish_message: Callable[[_Message], None],
            buffered_message: _Message = _SENTINEL,
    ) -> Optional[_Message]:
        for next_message in messages:
            if buffered_message is not cls._SENTINEL:
                publish_message(message=buffered_message)
            buffered_message = next_message
        if buffered_message is cls._SENTINEL:
            return None
        return buffered_message
