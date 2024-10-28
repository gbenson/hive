import json
import logging

from pika import BasicProperties
from pika.spec import Basic

from hive.messaging import Channel

logger = logging.getLogger(__name__)
d = logger.info


class ReactionManager:
    def __init__(self):
        self._reaction_for = {}

    def start_story(
            self,
            channel: Channel,
            event_id: str,
            success_reaction: str = "👍",
            #working_reaction: str = "⋯",
    ):
        self._reaction_for[event_id] = success_reaction
        #self._send_reaction(channel, event_id, working_reaction)

    def on_event(
            self,
            channel: Channel,
            method: Basic.Deliver,
            properties: BasicProperties,
            body: bytes,
    ):
        content_type = properties.content_type
        if content_type != "application/json":
            raise ValueError(content_type)
        event = json.loads(body)
        origin = event.get("meta", {}).get("origin", {})
        if origin.get("channel") != "matrix":
            return
        event_id = origin["event_id"]
        reaction = self._reaction_for.pop(event_id, None)
        if not reaction:
            return
        self._send_reaction(channel, event_id, reaction)

    def _send_reaction(self, channel: Channel, event_id: str, reaction: str):
        d('%s: sending "%s"', event_id, reaction)
        channel.publish_request(
            message={
                "reaction": reaction,
                "receiver": {
                    "event_id": event_id,
                },
            },
            routing_key="matrix.reaction.send.requests",
        )


# XXX such a hack!
reaction_manager = ReactionManager()
