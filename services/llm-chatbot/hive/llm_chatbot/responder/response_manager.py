import logging

from dataclasses import KW_ONLY, dataclass
from datetime import timedelta
from functools import cached_property
from typing import Any, ContextManager, Optional

from typing_extensions import Self

from hive.common.units import SECOND
from hive.messaging import Channel, Connection, blocking_connection

logger = logging.getLogger(__name__)
d = logger.debug


@dataclass
class ResponseManager:
    _: KW_ONLY
    default_user_typing_timeout: timedelta = 30 * SECOND

    _cctx: Optional[ContextManager[Connection]] = None
    conn: Optional[Connection] = None
    channel: Optional[Channel] = None

    def __enter__(self) -> Self:
        if not self.channel and not self.conn:
            self._cctx = blocking_connection()
            self.conn = self._cctx.__enter__()
        try:
            self.on_enter()
            return self
        except Exception as e:
            self.__exit__(type(e), e, e.__traceback__)
            raise

    def __exit__(self, *exc_info: Any) -> Optional[bool]:
        try:
            return self.on_exit(*exc_info)
        finally:
            if self._cctx:
                self._cctx.__exit__(*exc_info)

    @cached_property
    def _channel(self) -> Channel:
        if self.channel:
            return self.channel
        if self.conn:
            return self.conn.channel()
        raise RuntimeError

    def on_enter(self) -> None:
        d("Entering response manager")
        self.set_user_typing(True)

    def on_exit(
            self,
            exc_type: Any,
            exc_val: Any,
            exc_tb: Any,
    ) -> Optional[bool]:
        d("Leaving response manager")
        if exc_type:
            self._channel.send_text("🤮")
        self.set_user_typing(False)
        return False  # we **didn't** handle the exception

    def send_text(self, text: str) -> None:
        self._channel.send_text(text)
        self.set_user_typing(True)

    def set_user_typing(self, timeout: timedelta | bool) -> None:
        if timeout is True:
            timeout = self.default_user_typing_timeout
        self._channel.set_user_typing(timeout)
