import re

from dataclasses import dataclass, field
from functools import cached_property

from hive.service import HiveService

from .database import Database


@dataclass(frozen=True)
class Streams:
    journal: str = "journal"
    requests: str = "requests"


@dataclass
class BaseService(HiveService):
    db: Database = field(default_factory=Database.connect)
    streams: Streams = field(default_factory=Streams)
    consumer: str = ""
    consumer_group: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.consumer:
            self.consumer = self.default_consumer
        if not self.consumer_group:
            self.consumer_group = self.default_consumer_group

    @cached_property
    def default_consumer(self) -> str:
        base = __name__.rpartition(".")[0] or __name__
        return _sub_nonword("-", base)

    @cached_property
    def default_consumer_group(self) -> str:
        base = _sub_nonword("-", type(self).__module__)
        return base.removeprefix(f"{self.default_consumer}-")


def _sub_nonword(repl: str, string: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", repl, string)
