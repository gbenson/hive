from dataclasses import dataclass, field
from functools import partial

from valkey import Valkey

from .schema import ContextID, Message

_valkey_factory = partial(Valkey.from_url, "valkey://valkey")


@dataclass
class Database:
    _vk: Valkey = field(default_factory=_valkey_factory)

    def update_context(self, context_id: ContextID, message: Message) -> None:
        """Append the updated fields to the context's command stream.
        """
        fields = {"cmd": "update", **message.as_key_value_pairs()}
        _ = fields.pop("content.type", None)
        self._vk.xadd(f"ctx:{context_id}:log", fields)
