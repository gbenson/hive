from __future__ import annotations

import json
import sys

from collections import defaultdict
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

from pika import BasicProperties
from pydantic import BaseModel, ConfigDict

from hive.chat_router import (
    Service as ChatRouter,
    service as _chat_router_service,
)
from hive.chat_router.matrix import RoomMessageEvent
from hive.common import httpx
from hive.messaging import Channel, Message
from hive.reading_list_updater import (
    Service as ReadingListUpdater,
    service as _reading_list_updater_service,
)


class CachedResponse(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    request_url: str
    url: str
    http_version: str
    status_code: int
    reason_phrase: str
    headers: list[tuple[str, str]]
    body: str

    def raise_for_status(self):
        if self.status_code == 200:
            print("\x1B[42;30m 200 \x1B[0m")
            return
        if self.status_code == 403:
            raise RuntimeError((self.status_code, self.reason_phrase))
        print("shit:", self.status_code, self.reason_phrase)
        raise SystemExit

    @property
    def extensions(self):
        return {"from_cache": True}

    @property
    def text(self):
        return self.body


@dataclass
class WebCache:
    root: Path = Path(__file__).parent.parent / "web"
    responses: dict[str, set[str]] = field(
        default_factory=partial(defaultdict, set),
    )

    def __post_init__(self):
        for path in self.root.glob("*/*/*.json"):
            response = CachedResponse.model_validate_json(path.read_text())
            response_json = response.model_dump_json()

            for url in {response.request_url, response.url}:
                if response_json in self.responses.get(url, ()):
                    continue
                self.responses[url].add(response_json)

    def get(self, url: str) -> CachedResponse:
        responses = list(map(
            CachedResponse.model_validate_json,
            self.responses.get(url, ())))

        if len(responses) == 1:
            return responses[0]
        if not responses:
            print(f"\x1B[41;30m {url} \x1B[0m")
            with open("404.log", "a") as fp:
                print(url, file=fp)
            r = httpx.get(url, follow_redirects=True)
            path = self.root / f"reloaded/20250918/{uuid4()}.json"
            path.write_text(json.dumps({
               "request_url": url,
               **httpx.response_as_json(r),
            }))
            r.extensions["from_cache"] = True
            return r

        print(f"\x1B[43;30m {url} | {len(responses)} \x1B[0m")

        texts = {r.body for r in responses}
        if len(texts) == 1:
            return responses[0]
        sizes = {len(t) for t in texts}
        if len(sizes) == 1:
            return responses[0]

        mean = sum(sizes) / len(sizes)
        mini = 100 * (1 - min(sizes) / mean)
        maxi = 100 * (max(sizes) / mean - 1)

        assert max((mini, maxi)) < 10
        return responses[0]


_chat_router_service.router = Mock()
_reading_list_updater_service.HiveWiki = Mock()
_reading_list_updater_service.httpx = WebCache()


@dataclass
class Primer:
    _chat_router: ChatRouter = field(
        default_factory=ChatRouter,
    )
    _reading_list_updater: ReadingListUpdater = field(
        default_factory=ReadingListUpdater,
    )

    @property
    def channel(self) -> Channel:
        return Channel(PrimerChannel(self))

    def process_matrix_event(self, message: Message):
        self._chat_router.on_matrix_event(self.channel, message)

    def process_matrix_request(self, message: Message):
        pass

    def process_readinglist_update_request(self, message: Message):
        self._reading_list_updater.on_update_request(self.channel, message)

    def process_llm_chatbot_request(self, message: Message):
        event_json = message.event().model_dump_json()
        with open("llm-chatbot-requests.jsonl", "a") as fp:
            print(event_json, file=fp)
        print(f"\x1B[34m{event_json}\x1B[0m")


@dataclass
class PrimerChannel:
    primer: Primer

    def exchange_declare(self, **kwargs):
        pass

    def basic_publish(
            self,
            *,
            exchange: str,
            routing_key: str,
            body: bytes,
            properties: BasicProperties,
            mandatory: bool,
    ):
        assert routing_key == ""
        assert mandatory is True
        message = Message(None, properties, body)

        exchange_parts = exchange.split(".")
        assert exchange_parts[0] == "hive"
        assert exchange_parts[-1] == "requests"
        request_type = "_".join(exchange_parts[1:-1])
        consumer_name = f"process_{request_type}_request"
        consume = getattr(self.primer, consumer_name)
        consume(message)


def as_chat_router_input(matrix_event_json: str) -> Message:
    matrix_event = RoomMessageEvent.model_validate_json(
        matrix_event_json,
    )
    cloudevent_json, content_type = Channel._encapsulate(
        routing_key="matrix.events",
        subject=matrix_event.type,
        data=matrix_event.model_dump(),
    )
    messagebus_message = Message(
        None,
        Mock(content_type=content_type),
        cloudevent_json,
    )
    return messagebus_message


def main():
    primer = Primer()
    for line in sys.stdin.readlines():
        message = as_chat_router_input(line)
        primer.process_matrix_event(message)
