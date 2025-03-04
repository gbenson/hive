import logging

from functools import cached_property
from threading import Thread
from typing import Any
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


class LLMInteraction(Thread):
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
                "model": "smollm2:135m",
                "messages": self.llm_context,
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
