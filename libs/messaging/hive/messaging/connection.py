from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from typing import Any, Optional, TYPE_CHECKING
from typing_extensions import Self

from pika import BlockingConnection as _PikaConnection

from .channel import Channel

if TYPE_CHECKING:
    from .typing import OnChannelOpenCallback


@dataclass
class Connection:
    _pika: _PikaConnection
    _: KW_ONLY
    on_channel_open: Optional[OnChannelOpenCallback] = None

    def __hash__(self) -> int:
        return id(self)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: Any) -> None:
        if self._pika.is_open:
            self._pika.close()

    def _channel(
            self,
            *,
            name: str = "",
            **kwargs: Any
    ) -> Channel:
        return Channel(self._pika.channel(**kwargs), name=name)

    def channel(
            self,
            *,
            name: str = "",
            confirm_delivery: bool = True,
            **kwargs: Any
    ) -> Channel:
        """Like :class:pika.channel.Channel` but with different defaults.

        :param name: Used by `Channel.consume_events()` to construct
             unique queue names.  May be required when more than one
             consumer with the same `Channel.consumer_name` may exist,
             which can happen if processes have multiple channels or
             if multiple processes share the same name.
        :param confirm_delivery: Whether to enable delivery confirmations.
            Hive's default is True.  Use `confirm_delivery=False` for the
            original Pika behaviour.
        """
        channel = self._channel(name=name, **kwargs)
        if confirm_delivery:
            channel._pika.confirm_delivery()  # Don't fail silently.
        if self.on_channel_open:
            self.on_channel_open(channel)
        return channel
