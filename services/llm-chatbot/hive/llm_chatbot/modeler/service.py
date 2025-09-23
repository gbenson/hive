import logging

from typing import Any

from hive.common import dynamic_cast

from ..service import BaseService
from .schema import Action

logger = logging.getLogger(__name__)
d = logger.info


class Service(BaseService):
    """The modeler service expands the journal into something more structured.
    """

    def run(self) -> None:
        self._run(
            stream=self.streams.journal,
            group=self.consumer_group,
            consumer=self.consumer,
        )

    def _run(self, *, stream: str, group: str, consumer: str) -> None:
        self.db.xgroup_create(stream, group, id=0, mkstream=True)

        while True:
            response = self.db.xreadgroup(
                group,
                consumer,
                {stream: ">"},
                count=100,
                block=30_000,  # 30 seconds
            )
            for _, entries in dynamic_cast(list, response):
                for entry in entries:
                    entry_id, values = entry
                    self.on_request(entry_id, values)
                    self.db.xack(stream, group, entry_id)

    def on_request(self, action_id: str, values: dict[str, Any]) -> None:
        d("Applying %s: %s", action_id, values)

        if (supplied_id := values.get("id")):
            logger.warning("%s: replacing id=%r", action_id, supplied_id)

        action = Action.model_validate({**values, "id": action_id})

        if not (execute_action := getattr(self, f"on_{action.type}", None)):
            raise NotImplementedError(action.type)

        execute_action(action)

    def on_upsert_message(self, action: Action) -> None:
        message = action.message
        msgid_key = f"msg:{message.id}:msgid"

        # This non-atomic shuffle works because only one thread
        # executes the journal.  It could be scaleed  by rekeying
        # for one-thread-per-context if it becomes a bottleneck.
        msgid = self.db.get(msgid_key)
        if (is_insert := not bool(msgid)):
            msgid = dynamic_cast(
                int,
                self.db.incr("last_msgid"),
            )
        else:
            msgid = dynamic_cast(str, msgid)

        msg_key = f"msg:{msgid}"
        self.db.hset(msg_key, mapping={
            field: str(value)
            for field, value in message.model_dump().items()
        })
        if not is_insert:
            return

        # Make the new message visible in the database.
        self.db.set(msgid_key, msgid)

        # Add the message to the context.
        context_id = action.context_id
        ctx_messages_key = f"ctx:{context_id}:msgs"
        self.db.zadd(ctx_messages_key, {str(msgid): action.monotonic_id})
