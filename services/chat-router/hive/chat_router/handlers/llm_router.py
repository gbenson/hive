from __future__ import annotations

import json
import logging

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from functools import cached_property
from html import escape
from threading import Thread
from typing import Any, Optional
from uuid import UUID

# from openai.types.chat import ChatCompletionMessageToolCall

from hive.chat import ChatMessage, tell_user
# from hive.common.llm import LLMToolbox, llm_tool
# from hive.common.openai import OpenAI
from hive.messaging import Channel, blocking_connection

# from ..handler import Handler

logger = logging.getLogger(__name__)
d = logger.info

ChatCompletionMessageToolCall = OpenAI = NotImplemented
Handler = LLMToolbox = type("XXXDisabled", (), {})
llm_tool = lambda f: f  # noqa: E731


class LLMHandler(Handler):
    @property
    def priority(self) -> int:
        return 98

    def handle(self, channel: Channel, message: ChatMessage) -> bool:
        interaction = LLMInteraction(message)
        d("LLM request: %s", interaction.api_request)
        interaction.start()
        return True


class LLMInteraction(LLMToolbox, Thread):
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

    def __init__(self, message: ChatMessage):
        self.chat_message = message
        if not self.user_prompt:
            raise ValueError
        self.api_client = OpenAI()
        super().__init__(
            name=f"LLM-interaction-{message.timestamp:%Y%m%d-%H%M%S}",
            daemon=True,
        )

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
    def api_request(self) -> dict[str, Any]:
        return {
            "model": "gpt-4o-mini",
            "messages": self.llm_context,
            "tools": self.llm_tools,
            "temperature": 0,
        }

    def run(self):
        d("%s: started", self.name)
        try:
            self._run()
        except Exception:
            logger.exception("%s: EXCEPTION", self.name)
        d("%s: stopped", self.name)

    def _run(self):
        response = self.api_client.chat.completions.create(**self.api_request)
        d("LLM response: %s", response.model_dump())

        if not response.choices:
            return

        choice = response.choices[0]
        message = choice.message
        tool_calls = list(self.parse_tool_calls(message.tool_calls))

        if choice.finish_reason != "tool_calls" or not tool_calls:
            if message.content:
                tell_user(
                    message.content,
                    in_reply_to=self.chat_message,
                )
            return

        with blocking_connection() as conn:
            self.dispatch_tool_calls(conn.channel(), tool_calls)

    def parse_tool_calls(
            self,
            tool_calls: Iterable[ChatCompletionMessageToolCall],
    ) -> Iterable[LLMToolCall]:
        for tool_call in tool_calls:
            try:
                yield LLMToolCall.from_ccm_tool_call(tool_call)
            except Exception:
                logger.exception("%s: EXCEPTION", self.name)

    def dispatch_tool_calls(
            self,
            channel: Channel,
            tool_calls: list[LLMToolCall],
    ):
        placeholder_uuids = [
            self.set_placeholder(channel, tool_call)
            for tool_call in tool_calls
        ]
        for placeholder_uuid, tool_call in zip(placeholder_uuids, tool_calls):
            self.dispatch_tool_call(
                channel,
                tool_call,
                response_uuid=placeholder_uuid,
            )

    def set_placeholder(
            self,
            channel: Channel,
            tool_call: LLMToolCall,
    ) -> Optional[UUID]:
        try:
            return self._set_placeholder(channel, tool_call)
        except Exception:
            logger.exception("%s: EXCEPTION", self.name)

    def _set_placeholder(
            self,
            channel: Channel,
            tool_call: LLMToolCall,
    ) -> UUID:
        return tell_user(
            text=tool_call.as_text(),
            html=tool_call.as_html(),
            in_reply_to=self.chat_message,
            channel=channel,
        ).uuid

    def dispatch_tool_call(
            self,
            channel: Channel,
            tool_call: LLMToolCall,
            response_uuid: Optional[UUID] = None,
    ):
        try:
            self._dispatch_tool_call(channel, tool_call, response_uuid)
        except Exception:
            logger.exception("%s: EXCEPTION", self.name)

    def _dispatch_tool_call(
            self,
            channel: Channel,
            tool_call: LLMToolCall,
            response_uuid: Optional[UUID],
    ):
        request = asdict(tool_call)
        if response_uuid:
            request["response_uuid"] = str(response_uuid)
        channel.publish(
            message=request,
            routing_key="mediawiki.lookup.requests",
        )


@dataclass
class LLMToolCall:
    function_name: str
    arguments: dict[str, Any]
    tool_call_id: Optional[str] = None

    @classmethod
    def from_ccm_tool_call(
            cls,
            tool_call: ChatCompletionMessageToolCall,
    ) -> LLMToolCall:
        func = tool_call.function
        return cls(
            tool_call_id=tool_call.id,
            function_name=func.name,
            arguments=json.loads(func.arguments),
        )

    def as_text(self) -> str:
        return str(TCTextFormatter(self))

    def as_html(self) -> str:
        return str(TCHTMLFormatter(self))


@dataclass
class TCTextFormatter:
    _tc: LLMToolCall

    def __str__(self) -> str:
        return f"[tool call: {self._name}({self._args})]"

    @property
    def _name(self) -> str:
        return self._tc.function_name

    @property
    def _args(self) -> str:
        return ", ".join(
            f"{self._arg_name(name)}={self._arg_value(value)}"
            for name, value in self._tc.arguments.items()
        )

    def _arg_name(self, name: str) -> str:
        return name

    def _arg_value(self, value: Any) -> str:
        return json.dumps(value)


class TCHTMLFormatter(TCTextFormatter):
    s1 = '<span class="unsent">'
    s2 = '<span class="unseen">'
    es = "</span>"

    def __str__(self) -> str:
        return f"{self.s1}{self.s2}{super().__str__()}{self.es}{self.es}"

    @property
    def _name(self) -> str:
        return f"{self.es}{escape(super()._name)}{self.s2}"

    def _arg_name(self, name: str) -> str:
        return escape(super()._arg_name(name))

    def _arg_value(self, value: Any) -> str:
        value = super()._arg_value(value)
        pfx = sfx = ""
        if value and (pfx := value[0]) in '"[{':
            sfx = value[-1]
            value = value[1:-1]

        return f"{escape(pfx)}{self.es}{escape(value)}{self.s2}{escape(sfx)}"
