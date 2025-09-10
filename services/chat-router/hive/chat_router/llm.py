from dataclasses import dataclass
from functools import partial
from typing import Any

from hive.common import blake2b_digest_uuid
from hive.messaging import Channel

from .request import Request


def _publish_request(
        channel: Channel,
        type: str,
        **kwargs: Any,
) -> None:
    channel.publish_request(
        routing_key="llm.chatbot.requests",
        type=f"net.gbenson.hive.llm_chatbot_{type}_request",
        **kwargs
    )


_update_context = partial(_publish_request, type="update_context")


@dataclass
class LLM:
    def update_context(
            self,
            channel: Channel,
            request: Request,
            *,
            role: str,
    ) -> None:
        _update_context(
            channel,
            time=request.time,
            data={
                "context_id": str(blake2b_digest_uuid(request.room_id)),
                "message": {
                    "id": str(blake2b_digest_uuid(request.event_id)),
                    "role": role,
                    "content": {
                        "type": "text",
                        "text": request.text,
                    },
                },
            },
        )
