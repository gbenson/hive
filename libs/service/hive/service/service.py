import logging
import sys

from abc import ABC, abstractmethod
from contextlib import suppress
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Optional

from hive.common import ArgumentParser
from hive.messaging import (
    Connection,
    blocking_connection,
    publisher_connection,
)
from hive.messaging.typing import ConnectionFactory, OnChannelOpenCallback

from .logging import maybe_enable_json_logging

logger = logging.getLogger(__name__)


@dataclass
class Service(ABC):
    argument_parser: Optional[ArgumentParser] = None
    on_channel_open: Optional[OnChannelOpenCallback] = None
    unparsed_arguments: Optional[list[str]] = None
    version_info: Optional[str] = None

    def make_argument_parser(self) -> ArgumentParser:
        parser = ArgumentParser()
        return parser

    def __post_init__(self) -> None:
        if not self.argument_parser:
            self.argument_parser = self.make_argument_parser()
        maybe_enable_json_logging()

        in_pytest = self.argument_parser.prog == "pytest"
        if self.unparsed_arguments is None:
            if in_pytest:
                self.unparsed_arguments = []
            else:
                self.unparsed_arguments = sys.argv[1:]
        self.args = self.argument_parser.parse_args(self.unparsed_arguments)

        if not self.version_info:
            self.version_info = self._init_version_info()
        logger.info("Starting %s", self.version_info)

    def _init_version_info(self) -> str:
        service_version = "0.0.0"
        service_package = type(self).__module__.removesuffix(".service")
        for prefix in (".", ".."):
            with suppress(Exception):
                version_module = import_module(
                    "{prefix}__version__",
                    service_package,
                )
                service_version = version_module.__version__
                break
        service_name = service_package.replace(".", "-").replace("_", "-")
        if service_version == "0.0.0":
            return service_name
        return f"{service_name} version {service_version}"

    @classmethod
    def main(cls, **kwargs: Any) -> None:
        service = cls(**kwargs)
        if not service.version_info:
            raise RuntimeError("__post_init__ masked?")
        service.run()

    @abstractmethod
    def run(self) -> None:
        raise NotImplementedError

    def blocking_connection(self, **kwargs: Any) -> Connection:
        return self._connect(blocking_connection, kwargs)

    def publisher_connection(self, **kwargs: Any) -> Connection:
        return self._connect(publisher_connection, kwargs)

    def _connect(
            self,
            connect: ConnectionFactory,
            kwargs: Any
    ) -> Connection:
        on_channel_open = kwargs.pop("on_channel_open", self.on_channel_open)
        return connect(on_channel_open=on_channel_open, **kwargs)
