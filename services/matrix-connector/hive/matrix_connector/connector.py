from dataclasses import dataclass
from functools import cached_property

from valkey import Valkey

from hive.service import HiveService


@dataclass
class ConnectorService(HiveService):
    valkey_url: str = "valkey://matrix-connector-valkey"

    @cached_property
    def _valkey(self) -> Valkey:
        return Valkey.from_url(self.valkey_url)
