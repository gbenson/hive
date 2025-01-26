import logging

from functools import cached_property
from threading import Thread
from typing import Any

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
        d("LLM request: %s", interaction.llm_request)
        interaction.start()
        return True


class LLMInteraction(Thread):
    def __init__(self, message: ChatMessage):
        self._channel = None
        self.chat_message = message
        if not self.user_prompt:
            raise ValueError
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
    def llm_request(self) -> dict[str, Any]:
        return {"messages": [
            {"role": "system",
             "content": self.SYSTEM_PROMPT},
            {"role": "user",
             "content": self.user_prompt},
        ]}

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
            request=self.llm_request,
            routing_key="local.llm.requests",
            correlation_id=str(self.chat_message.uuid),
            reply_to=responses_queue,
        )

        channel.start_consuming()

    def on_rpc_response(self, channel: Channel, message: Message):
        response = message.json()
        d("%s: received: %s", self.name, response)
        if response.get("status") == "received":
            tell_user(
                "✨The LLM is thinking...",
                in_reply_to=self.chat_message,
                channel=channel,
            )
            return
        try:
            self.on_response(channel, response)
        except Exception:
            logger.exception("%s: EXCEPTION", self.name)
        channel.stop_consuming()

    def on_response(self, channel: Channel, response: dict[str, Any]):
        message = response["message"]
        if (role := message["role"]) != "assistant":
            raise ValueError(role)
        if not (content := message["content"]):
            raise ValueError
        tell_user(content, in_reply_to=self.chat_message, channel=channel)
