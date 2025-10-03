import logging

from dataclasses import KW_ONLY, dataclass
from datetime import datetime, timedelta
from functools import cached_property
from typing import Any, ContextManager, Optional

from typing_extensions import Self

from hive.common.units import MILLISECOND, SECOND
from hive.messaging import Channel, Connection, blocking_connection

logger = logging.getLogger(__name__)
d = logger.info


@dataclass
class ResponseManager:
    _: KW_ONLY
    _cctx: Optional[ContextManager[Connection]] = None
    conn: Optional[Connection] = None
    channel: Optional[Channel] = None
    _typing_deadline: Optional[datetime] = None

    user_typing_timeout: timedelta = 30 * SECOND

    # Don't extend timeouts by less than this amount.
    min_extension: timedelta = 10 * SECOND

    # Don't cancel timeouts shorter than this.
    min_cancellation: timedelta = 500 * MILLISECOND

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
        self.set_user_typing()

    def on_exit(
            self,
            exc_type: Any,
            exc_val: Any,
            exc_tb: Any,
    ) -> Optional[bool]:
        d("Leaving response manager")
        if exc_type:
            self._channel.send_text("🤮")
        self.cancel_user_typing()
        return False  # we **didn't** handle the exception

    def send_text(self, text: str) -> None:
        self._channel.send_text(text)
        self.set_user_typing()

    def set_user_typing(self) -> None:
        want_timeout = self.user_typing_timeout
        want_deadline = datetime.now() + want_timeout

        have_deadline = self._typing_deadline
        if have_deadline is not None:
            extension = want_deadline - have_deadline
            if extension < self.min_extension:
                return

        d("Setting %s timeout", want_timeout)
        self._channel.set_user_typing(want_timeout)
        self._typing_deadline = want_deadline
        d("Typing deadline now %s", self._typing_deadline)

    def cancel_user_typing(self) -> None:
        have_deadline = self._typing_deadline
        if have_deadline is None:
            return

        have_timeout = have_deadline - datetime.now()
        if have_timeout > self.min_cancellation:
            d("Cancelling remaining %s timeout", have_timeout)
            self._channel.set_user_typing(False)

        self._typing_deadline = None
        d("Typing deadline now %s", self._typing_deadline)
