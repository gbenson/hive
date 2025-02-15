import logging

from collections.abc import Iterable
from dataclasses import dataclass
from functools import cached_property
from inspect import get_annotations, stack
from threading import Thread
from typing import Any, Callable, ClassVar, TypeVar
from uuid import uuid4

from hive.chat import ChatMessage, tell_user
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


class LLMToolbox:
    @property
    def llm_tools(self) -> list[dict[str, Any]]:
        locs = [(frame.filename, frame.lineno) for frame in stack()]
        if locs[1] in locs[2:]:
            return []  # recursion!
        return list(self._llm_tools)

    @property
    def _llm_tools(self) -> Iterable[dict[str, Any]]:
        for name in dir(self):
            if name.startswith("_"):
                continue
            candidate = getattr(self, name)
            if not getattr(candidate, "__llm_tool__", False):
                continue
            yield LLMTool(name, candidate).definition


@dataclass
class LLMTool:
    name: str
    func: Callable

    @property
    def definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    @property
    def description(self) -> str:
        return self.func.__doc__.partition(":param ")[0].strip()

    @property
    def parameters(self) -> dict[str, Any]:
        params = dict(self._parameters)
        return {
            "type": "object",
            "properties": params,
            "required": list(params.keys()),
        }

    @property
    def _parameters(self) -> Iterable[str, dict[str, Any]]:
        for param_doc in self.func.__doc__.split(":param ")[1:]:
            name, description = param_doc.split(":", 1)
            _type = get_annotations(self.func)[name]
            yield name, {
                "type": self._TYPE_NAMES[_type],
                "description": description.strip(),
            }

    _TYPE_NAMES: ClassVar[dict[TypeVar, str]] = {
        int: "integer",
        str: "string",
    }


def llm_tool(func):
    func.__llm_tool__ = True
    return func


class LLMInteraction(LLMToolbox, Thread):
    def __init__(self, message: ChatMessage):
        self.chat_message = message
        if not self.user_prompt:
            raise ValueError
        super().__init__(
            name=f"LLM-interaction-{message.timestamp:%Y%m%d-%H%M%S}",
            daemon=True,
        )
        self.response_uuid = uuid4()
        self.response_text = ""

    SYSTEM_PROMPT = "You are Hive, a helpful assistant."

    @cached_property
    def user_prompt(self) -> str:
        if (text := self.chat_message.text):
            return text.strip()
        raise NotImplementedError("html2text")

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
                "model": "qwen2.5:0.5b",
                "messages": self.llm_context,
                "tools": self.llm_tools,
            },
        }

    @property
    def responses_queue_basename(self) -> str:
        return self.name.lower().replace("-", ".", 2)

    def run(self):
        d("%s: started", self.name)
        try:
            with blocking_connection() as conn:
                self._run(conn.channel())
        except Exception:
            logger.exception("%s: EXCEPTION", self.name)
        d("%s: stopped", self.name)

    def _run(self, channel: Channel):
        responses_queue = channel.queue_declare(
            self.responses_queue_basename,
            exclusive=True,
        ).method.queue

        channel.consume_rpc_responses(
            queue=responses_queue,
            on_message_callback=self.on_rpc_response,
        )

        channel.publish_rpc_request(
            request=self.ollama_api_request,
            routing_key="ollama.api.requests",
            correlation_id=str(self.chat_message.uuid),
            reply_to=responses_queue,
        )

        channel.start_consuming()

    def on_rpc_response(self, channel: Channel, message: Message):
        try:
            response = message.json()
            d("%s: received: %s", self.name, response)
            self.on_response(channel, response)
            if not response.get("done", True):
                return  # keep consuming
        except Exception:
            logger.exception("%s: EXCEPTION", self.name)
        channel.stop_consuming()

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

    @llm_tool
    def get_email_address_for_service(self, service: str):
        """Get the email address for a service.

        :param service: The service to get the email address for.
        """

    @llm_tool
    def get_password_for_service(self, service: str):
        """Get the password for a service.

        :param service: The service to get the password for.
        """
