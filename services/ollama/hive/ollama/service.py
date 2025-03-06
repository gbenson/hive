from __future__ import annotations

import json
import logging

from dataclasses import dataclass
from typing import Any, ClassVar, Optional
from urllib.parse import urlparse, urljoin

import requests

from hive.common import ArgumentParser
from hive.messaging import Channel, Message
from hive.service import HiveService

logger = logging.getLogger(__name__)
d = logger.info


@dataclass
class Flow:
    correlation_id: str
    channel: Channel
    responses_queue: str
    _sent_done: bool = False

    def __str__(self) -> str:
        return self.correlation_id  # for d("%s: ...", flow, ...)

    def __enter__(self) -> Flow:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            error = f"{exc_type.__name__}: {exc_val}"
        elif not self._sent_done:
            error = "Unterminated response"
        else:
            return
        self.publish_response({"error": error, "done": True})

    def publish_response(self, response: dict[str, Any]) -> None:
        self.channel.publish_event(
            message=response,
            correlation_id=self.correlation_id,
            routing_key=self.responses_queue,
        )
        if not response.get("done"):
            return
        self._sent_done = True


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
            channel.consume_requests(  # XXX consume_flow_requests
                queue=self.requests_queue,
                on_message_callback=self.on_request,
            )
            channel.start_consuming()

    def on_request(self, channel: Channel, message: Message) -> None:
        responses_queue = self.responses_queue
        with Flow(message.correlation_id, channel, responses_queue) as flow:
            self._on_request(flow, message.json())

    def _on_request(self, flow: Flow, request: dict[str, Any]) -> None:
        d("%s: Request: %s", flow, request)

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
        r.raise_for_status()

        for line in r.iter_lines():
            flow.publish_response(json.loads(line))
