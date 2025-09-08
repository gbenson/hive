from dataclasses import dataclass
from typing import Any

from hive.messaging import Channel

from .request import Request


@dataclass
class LLM:
    def add_to_context(
            self,
            channel: Channel,
            request: Request,
            *,
            role: str
    ) -> None:
        self._publish_llm_request(
            channel,
            request_type="add_to_context",
            time=request.time,
            data={
                "role": role,
                "type": "text/plain",
                "content": request.text,
                "origin": request.origin,
            },
        )

    @staticmethod
    def _publish_llm_request(
            channel: Channel,
            request_type: str,
            **kwargs: Any
    ) -> None:
        channel.publish_request(
            type=f"net.gbenson.hive.chatbot_{request_type}_request",
            routing_key="chatbot.requests",
            **kwargs
        )
