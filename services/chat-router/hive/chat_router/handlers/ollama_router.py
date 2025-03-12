from __future__ import annotations

import logging
import re

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum, auto
from functools import cached_property, lru_cache, partial
from itertools import chain
from textwrap import dedent
from threading import Thread
from typing import Any, Optional
from uuid import uuid4

from spellchecker import SpellChecker

from hive.chat import ChatMessage, tell_user, tell_user_errors
from hive.common import read_config
from hive.common.units import MINUTE, SECOND
from hive.messaging import Channel, Message, blocking_connection

from ..handler import Handler

logger = logging.getLogger(__name__)
d = logger.info


class Intent(Enum):
    CREDS = auto()
    IMAGE = auto()
    WIFI = auto()


class LLMHandler(Handler):
    @property
    def priority(self) -> int:
        return 99

    def handle(self, channel: Channel, message: ChatMessage) -> bool:
        with tell_user_errors(in_reply_to=message):
            guessed_intent = self.guess_intent(message.text)
            interaction = LLMInteraction(message, guessed_intent)
            d("LLM request: %r", interaction.user_prompt)
            interaction.start()
        return True

    INTENT_KEYWORDS = {
        Intent.CREDS: {
            "addr", "address",
            "credentials", "creds",
            "email",
            "id",
            "log", "login", "logon",
            "mail",
            "name",
            "pass", "passwd", "password",
            "sign",
            "user", "userid", "username",
        },
        Intent.IMAGE: {
            "coloring", "colouring",
            "draw", "drawing",
            "image", "imagine",
            "paint", "painting",
            "photo", "photograph",
            "picture",
            "render",
        },
        Intent.WIFI: {
            "fi",
            "internet",
            "net", "network",
            "wi", "wifi", "wireless",
        },
    }

    KEYWORD_INTENTS = dict(
        chain.from_iterable(
            ((keyword, intent)
             for keyword in keywords)
            for intent, keywords in INTENT_KEYWORDS.items())
    )

    KEYWORD_SPLIT = re.compile(r"\W+")

    def guess_intent(self, query: str) -> Optional[Intent]:
        words = self.KEYWORD_SPLIT.split(query.lower())
        if (intent := self._guess_intent(words)):
            return intent
        return self._guess_intent(words, spellcheck=True)

    def _guess_intent(
            self,
            words: set[str],
            spellcheck: bool = False,
    ) -> Optional[Intent]:
        scores = defaultdict(int)
        for word in words:
            if (intent := self.KEYWORD_INTENTS.get(word)):
                scores[intent] += 1
                continue
            if not spellcheck:
                continue
            if (corrected_word := self._spellchecked_keyword(word)):
                intent = self.KEYWORD_INTENTS[corrected_word]
                scores[intent] += 1

        scores = list(sorted(
            (score, intent)
            for intent, score in scores.items()
        ))
        match len(scores):
            case 0:
                return None
            case 1:
                return scores[-1][1]
            case _ if scores[-1][0] > scores[-2][0]:
                return scores[-1][1]
            case _:
                return None

    @cached_property
    def _spellcheck(self) -> SpellChecker:
        return SpellChecker()

    @lru_cache
    def _spellchecked_keyword(self, word: str) -> Optional[str]:
        if len(word) < 3:
            return None
        candidates = self._spellcheck.candidates(word)
        if not candidates:
            return None
        candidates = [
            candidate
            for candidate in candidates
            if candidate in self.KEYWORD_INTENTS
        ]
        if len(candidates) != 1:
            return None
        return candidates[0]


class LLMInteraction(Thread):
    def __init__(
            self,
            message: ChatMessage,
            guessed_intent: Optional[Intent],
            config_key: str = "ollama-router",
            config: dict[str, Any] | None = None,
            model: str | None = None,
            channel_name: str | None = None,
            requests_queue: str = "ollama.api.requests",
            responses_queue: str = "ollama.api.responses",
            consume_timeout: timedelta = 5 * SECOND,
            overall_timeout: timedelta = 1 * MINUTE,
    ):
        self.chat_message = message
        if not self.user_prompt:
            raise ValueError
        super().__init__(
            name=f"LLM-interaction-{message.timestamp:%Y%m%d-%H%M%S}",
            daemon=True,
        )
        if not channel_name:
            channel_name = f"{message.timestamp:%Y%m%d.%H%M%S}"
        self.channel_name = channel_name
        self.config_key = config_key
        self._config = config
        self._model = model
        self.requests_queue = requests_queue
        self.responses_queue = responses_queue
        self.consume_timeout = consume_timeout
        self.overall_timeout = overall_timeout
        self._on_response = None

    @cached_property
    def config(self) -> dict[str, Any]:
        if (c := self._config) is not None:
            return c
        try:
            return read_config(self.config_key)
        except KeyError:
            return {}

    @cached_property
    def model(self) -> dict[str, Any]:
        if (m := self._model) is not None:
            return m
        return self.config.get("model", "gbenson/qwen2.5-0.5b-instruct:q2_k")

    @cached_property
    def user_prompt(self) -> str:
        if (text := self.chat_message.text):
            return text.strip()
        raise NotImplementedError("html2text")

    def run(self):
        d("%s: started", self.name)
        with tell_user_errors(in_reply_to=self.chat_message) as reporter:
            with blocking_connection() as conn:
                channel = conn.channel(name=self.channel_name)
                reporter.channel = channel
                self._run(channel)
        d("%s: stopped", self.name)

    def _run(self, channel: Channel):
        # exclusive=True means the queue auto-deletes when this
        # interaction closes its connection, which should cause
        # an error in the sender and cause it to stop streaming
        # from ollama.  **should**.
        channel.consume_events(
            queue=self.responses_queue,
            on_message_callback=self.on_response,
            exclusive=True,
        )

        # consume_by makes sure we don't build up a backlog
        # (if no ollama is running then drop the now-unwanted
        # responses when it comes back up).
        consume_by = self.chat_message.timestamp + self.consume_timeout
        intent = self._run_flow(
            channel,
            IntentClassifier(
                model=self.model,
                user_prompt=self.user_prompt,
                consume_by=consume_by,
                timeout=self.overall_timeout,
            ),
        )
        d("%s: got intent: %r", self.name, intent)
        tell_user(
            f"{self.name}: got intent: {intent}",
            channel=channel,
            in_reply_to=self.chat_message,
        )
        raise NotImplementedError

    def _run_flow(
            self,
            channel: Channel,
            flow: OllamaRequestFlow,
    ) -> Any:
        self._on_response = flow._on_response
        return flow.run(channel, self.requests_queue)

    def on_response(self, channel: Channel, message: Message):
        d("Response: %s", message)
        flow_is_complete = True
        try:
            flow_is_complete = self._on_response(channel, message)
        finally:
            if flow_is_complete:
                channel.stop_consuming()


@dataclass
class CommandFlow(ABC):
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    timeout: Optional[timedelta] = 5 * SECOND  # max time to wait for response
    deadline: Optional[datetime] = None  # fail if response not recieved by
    consume_by: Optional[datetime] = None  # consumer should discard after
    start_time: Optional[datetime] = None
    is_running: bool = False
    response: Any = None
    seen_responses: int = 0

    @abstractmethod
    def publish_request(self, channel: Channel, requests_queue: str):
        """Initiate the flow."""

    @abstractmethod
    def on_response(self, channel: Channel, message: Message) -> bool:
        """Return True if flow is complete, False to await more responses."""

    def run(self, channel: Channel, requests_queue: str) -> Any:
        """Run to completion.
        """
        self.start(channel, requests_queue)
        channel.start_consuming()
        return self.response

    def start(self, channel: Channel, requests_queue: str):
        """Start the flow.
        """
        if self.start_time:
            raise RuntimeError
        self.start_time = datetime.now(tz=timezone.utc)

        if self.timeout and not self.deadline:
            self.deadline = self.start_time + self.timeout

        if (deadline := self.deadline):
            if (consume_by := self.consume_by):
                if consume_by > deadline:
                    self.consume_by = deadline
            else:
                self.consume_by = deadline

            timeout = deadline - self.start_time
            channel.connection.call_later(
                timeout / timedelta(seconds=1),
                partial(self._maybe_timeout, channel),
            )

        self.publish_request(
            FlowChannel(self.correlation_id, channel),
            requests_queue,
        )
        self.is_running = True

    def _on_response(self, channel: Channel, message: Message):
        if message.correlation_id != self.correlation_id:
            d("%s != %s", message.correlation_id, self.correlation_id)
            return
        self.seen_responses += 1

        try:
            if self.on_response(channel, message):
                self.stop(channel)
        except Exception:
            if self.is_running:
                self.stop(channel)
            raise

    def _maybe_timeout(self, channel: Channel):
        if self.seen_responses:
            return
        logger.error("TimeoutError: Deadline exceeded")
        self.stop(channel)

    def stop(self, channel: Channel):
        """Stop the flow.
        """
        if not self.is_running:
            raise RuntimeError
        self.is_running = False
        channel.stop_consuming()


@dataclass
class FlowChannel:
    correlation_id: str
    channel: Channel

    def publish_request(self, **kwargs):
        d("Request: %s", {"correlation_id": self.correlation_id, **kwargs})
        return self.channel.publish_request(
            correlation_id=self.correlation_id,
            **kwargs
        )


@dataclass
class OllamaRequestFlow(CommandFlow):
    model: str | None = None
    timeout: Optional[timedelta] = 1 * MINUTE

    @property
    @abstractmethod
    def ollama_api_request(self) -> dict[str, Any]:
        """Request to send to initiate the flow."""

    def publish_request(self, channel: Channel, requests_queue: str):
        channel.publish_request(
            message=self.ollama_api_request,
            routing_key=requests_queue,
            consume_by=self.consume_by,
        )


@dataclass
class IntentClassifier(OllamaRequestFlow):
    user_prompt: str = ""
    response: str | None = None

    SYSTEM_PROMPT = (
        """\
        You are a helpful assistant.  You will be provided with queries
        and requests.  Classify each by responding with exactly one of
        the following words:

        1. If the input is a request for a coloring page, output "COLORING".
        2. If the input is another image generation request, output "IMAGE".
        3. If the input is a request to create, generate or look up credentials
           (email addresses, usernames, passwords, etc), output "CREDS".
        4. If the input mentions networking or wifi, output "NET".
        5. If none of the above are appropriate, output "OTHER".

        Notes:
        - Requests to "imagine" are usually image generation requests.
        """
    )

    @cached_property
    def llm_context(self) -> dict[str, Any]:
        system_prompt = dedent(self.SYSTEM_PROMPT).rstrip()
        preface, sep, lists = system_prompt.partition("\n\n")
        preface = " ".join(preface.split())
        system_prompt = f"{preface}{sep}{lists}"
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": self.user_prompt},
        ]

    @property
    def ollama_api_request(self) -> dict[str, Any]:
        result = {
            "method": "POST",
            "request_uri": "/api/chat",
            "data": {
                "model": self.model,
                "messages": self.llm_context,
                "options": {
                    "temperature": 0,
                },
                "stream": False,
            },
            "correlation_id": self.correlation_id,
        }
        if (consume_by := self.consume_by):
            result["consume_by"] = str(consume_by)
        return result

    def on_response(self, channel: Channel, message: Message) -> bool:
        response = message.json()
        d("received: %s", response)
        if (error := response.get("error")):
            raise RuntimeError(error)
        if not response.get("done", True):
            tell_user(message.body.decode("utf-8"), channel=channel)
            return False  # keep consuming
        message = response["message"]
        if (role := message["role"]) != "assistant":
            raise ValueError(role)
        self.response = message["content"]
        return True  # stop consuming
