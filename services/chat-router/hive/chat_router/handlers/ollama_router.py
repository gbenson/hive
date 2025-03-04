from __future__ import annotations

import logging

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property
from textwrap import dedent
from threading import Thread
from typing import Any
from uuid import uuid4

from hive.chat import ChatMessage, tell_user
from hive.common import read_config
from hive.messaging import Channel, Message, blocking_connection

from ..handler import Handler

logger = logging.getLogger(__name__)
d = logger.info


class LLMHandler(Handler):
    @property
    def priority(self) -> int:
        return 99

    def handle(self, channel: Channel, message: ChatMessage) -> bool:
        interaction = LLMInteraction(message)
        d("LLM request: %s", interaction.ollama_api_request)
        interaction.start()
        return True


class LLMInteraction(Thread):
    def __init__(
            self,
            message: ChatMessage,
            config_key: str = "ollama",
            config: dict[str, Any] | None = None,
            model: str | None = None,
            requests_queue: str = "ollama.api.requests",
            responses_queue: str = "ollama.api.responses",
    ):
        self.chat_message = message
        if not self.user_prompt:
            raise ValueError
        super().__init__(
            name=f"LLM-interaction-{message.timestamp:%Y%m%d-%H%M%S}",
            daemon=True,
        )
        self.config_key = config_key
        self._config = config
        self._model = model
        self.requests_queue = requests_queue
        self.responses_queue = responses_queue
        self._on_response = None

    @cached_property
    def config(self) -> dict[str, Any]:
        if (c := self._config) is not None:
            return c
        return read_config(self.config_key)

    @cached_property
    def model(self) -> dict[str, Any]:
        if (m := self._model) is not None:
            return m
        return self.config.get("model", "gbenson/hive")

    @cached_property
    def user_prompt(self) -> str:
        if (text := self.chat_message.text):
            return text.strip()
        raise NotImplementedError("html2text")

    def run(self):
        d("%s: started", self.name)
        try:
            with blocking_connection() as conn:
                self._run(conn.channel())
        except Exception:
            logger.exception("%s: EXCEPTION", self.name)
        d("%s: stopped", self.name)

    def _run(self, channel: Channel):
        channel.consume_events(
            queue=self.responses_queue,
            on_message_callback=self.on_response,
        )

        consume_by = self.chat_message.timestamp + timedelta(seconds=5)
        intent = self._run_flow(
            channel,
            IntentClassifier(
                model=self.model,
                user_prompt=self.user_prompt,
                consume_by=consume_by,
            ),
        )
        d("%s: got intent: %r", self.name, intent)
        raise NotImplementedError

    def _run_flow(
            self,
            channel: Channel,
            flow: CommandFlow,
    ) -> Any:
        if not flow.requests_queue:
            flow.requests_quete = self.requests_queue
        if not flow.responses_queue:
            flow.responses_quete = self.responses_queue

        self._on_response = flow.on_response
        flow.publish_request(channel, self.responses_queue)
        channel.start_consuming()

        return flow.response

    def on_response(self, channel: Channel, message: Message):
        flow_is_complete = True
        try:
            flow_is_complete = self._on_response(channel, message)
        finally:
            if flow_is_complete:
                channel.stop_consuming()


@dataclass
class CommandFlow(ABC):
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    requests_queue: Optional[str] = None
    responses_queue: Optional[str] = None
    consume_by: Optional[datetime] = None

    @abstractmethod
    def publish_request(self, channel: Channel, responses_queue: str):
        """Initiate the flow."""

    @abstractmethod
    def on_response(self, channel: Channel, message: Message) -> bool:
        """Return True if flow is complete, False to await more responses."""


class OllamaRequestFlow(CommandFlow):
    model: str | None = None

    @property
    @abstractmethod
    def ollama_api_request(self) -> dict[str, Any]:
        """Request to send to initiate the flow."""

    def publish_request(self, channel: Channel, responses_queue: str):
        channel.publish_request(
            request=self.ollama_api_request,
            routing_key=self.requests_queue,
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
            result["consume_by"] = consume_by
        return result

    def on_response(self, channel: Channel, message: Message) -> bool:
        try:
            response = message.json()
            d("%s: received: %s", self.interaction_name, response)
            if response.get("error"):
                raise RuntimeError(response)
            message = response["message"]
            if (role := message["role"]) != "assistant":
                raise ValueError(role)
            self.response = message["content"]
        finally:
            channel.stop_consuming()


class OldFlowBits:
    def __init__(self):
        self.response_uuid = uuid4()
        self.response_text = ""

    SYSTEM_PROMPT = "You are Hive, a helpful assistant."

    @cached_property
    def llm_context(self) -> dict[str, Any]:
        return [
            {"role": "system",
             "content": self.SYSTEM_PROMPT},
            {"role": "user",
             "content": self.user_prompt},
        ]

    @cached_property
    def ollama_api_request(self) -> dict[str, Any]:
        return {
            "method": "POST",
            "request_uri": "/api/chat",
            "data": {
                "model": self.model,
                "messages": self.llm_context,
            },
        }

    def on_response(self, channel: Channel, message: Message):
        try:
            response = message.json()
            d("%s: received: %s", self.interaction_name, response)
            self.on_response(channel, response)
            if response.get("error"):
                raise RuntimeError(response)
            if not response.get("done", True):
                return  # keep consuming
            channel.stop_consuming()
        except Exception:
            channel.stop_consuming()
            raise

    def on_response(self, channel: Channel, response: dict[str, Any]):
        if (error_message := response.get("error")):
            tell_user(
                f"error: {error_message}",
                in_reply_to=self.chat_message,
                channel=channel,
            )
            response["done"] = True  # hack
            return

        message = response["message"]
        if (role := message["role"]) != "assistant":
            raise ValueError(role)
        self.response_text += message["content"]
        tell_user(
            self.response_text,
            timestamp=response["created_at"],
            uuid=self.response_uuid,
            in_reply_to=self.chat_message,
            channel=channel,
        )
