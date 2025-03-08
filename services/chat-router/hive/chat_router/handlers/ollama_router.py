from __future__ import annotations

import logging

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import cached_property, partial
from textwrap import dedent
from threading import Thread
from typing import Any, Optional
from uuid import uuid4

from hive.chat import ChatMessage, tell_user, tell_user_errors
from hive.common import read_config
from hive.common.units import MINUTE, SECOND
from hive.messaging import Channel, Message, blocking_connection

from ..handler import Handler

logger = logging.getLogger(__name__)
d = logger.info


class LLMHandler(Handler):
    @property
    def priority(self) -> int:
        return 99

    def handle(self, channel: Channel, message: ChatMessage) -> bool:
        with tell_user_errors(in_reply_to=message):
            interaction = LLMInteraction(message)
            d("LLM request: %r", interaction.user_prompt)
            interaction.start()
        return True


class LLMInteraction(Thread):
    def __init__(
            self,
            message: ChatMessage,
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
        You are Hive, a helpful assistant.  You will be provided with
        customer service queries.  Classify each query into a primary
        category and a secondary category.  Provide your output in
        JSON format with the keys: primary and secondary.

        Primary categories:
        - Credential Management
        - Image Generation
        - Technical Support
        - General Assistance

        Credential Management secondary categories:
        - Email address creation or lookup
        - Password generation or lookup
        - Username lookup

        Image Generation secondary categories:
        - Generate colouring page
        - Other image generation

        Technical Support secondary categories:
        - Enable wifi
        - Disable wifi

        General Inquiry secondary categories:
        - Question answering
        - Other enquiries
        - Other conversation
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
                "format": {
                    "type": "object",
                    "properties": {
                        "primary": {"type": "string"},
                        "secondary": {"type": "string"},
                    },
                    "required": ["primary", "secondary"],
                },
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
