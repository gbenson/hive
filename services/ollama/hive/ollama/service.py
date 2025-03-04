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
    requests_queue: str = "ollama.api.requests"
    responses_queue: str = "ollama.api.responses"

    def make_argument_parser(self) -> ArgumentParser:
        parser = super().make_argument_parser()
        parser.add_argument(
            "--ollama-api-url",
            metavar="URL",
            default=self.DEFAULT_API_URL,
            help=(f"URL to proxy requests to"
                  f" [default: {self.DEFAULT_API_URL}]"),
        )
        return parser

    def __post_init__(self):
        super().__post_init__()
        if not self.ollama_api_url:
            self.ollama_api_url = self.args.ollama_api_url

    def run(self):
        with self.blocking_connection() as conn:
            channel = conn.channel()
            channel.consume_requests(
                queue=self.requests_queue,
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
                channel.publish_event,
                routing_key=self.responses_queue,
                correlation_id=correlation_id,
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
        publish_message(message=buffered_message)
        return buffered_message
