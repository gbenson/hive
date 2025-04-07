from __future__ import annotations

import logging

from dataclasses import dataclass
from html import escape
from threading import current_thread, main_thread
from typing import Optional
from uuid import UUID

from hive.messaging import Channel

from .message import ChatMessage
from .util import publish_event
from .v2 import send_text

logger = logging.getLogger(__name__)
d = logger.info


def tell_user(
        text: str | ChatMessage,
        *,
        channel: Optional[Channel] = None,
        **kwargs
) -> None:
    """Send a ChatMessage.
    """
    if isinstance(text, ChatMessage):
        # Support using tell_user to emit chat.messages from the USER
        # - reading list updater does this to decorate links with HTML
        # - matrix-transitioner does this with received matrix.events
        if kwargs:
            raise ValueError(kwargs)
        message = text
        # Also support using tell_user to emit chat.messages from HIVE
        # (temporarily?)
        # if message.sender == "hive":
        #     raise ValueError("Use v2 interface")
        publish_event(
            message=message.json(),
            routing_key="chat.messages",
            channel=channel,
        )
        return

    _ = kwargs.pop("html", None)  # XXX implement
    _ = kwargs.pop("in_reply_to", None)  # XXX implement?
    if kwargs:
        raise ValueError(kwargs)
    send_text(text, channel=channel)


@dataclass
class tell_user_errors:
    channel: Optional[Channel] = None
    in_reply_to: Optional[str | UUID | ChatMessage] = None

    def __enter__(self) -> tell_user_errors:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if not exc_type:
            return

        message_prefix = self._message_prefix

        logger.exception(f"{message_prefix}EXCEPTION")

        message = f"{message_prefix}{exc_type.__name__}: {exc_val}"

        tell_user(
            text=message,
            html=self._message_as_html(message),
            in_reply_to=self.in_reply_to,
            channel=self.channel,
        )

    @property
    def _message_prefix(self) -> str:
        if (thread := current_thread()) is main_thread():
            return ""
        if not (thread_name := thread.name):
            return ""
        return f"{thread_name}: "

    @staticmethod
    def _message_as_html(text: str) -> str:
        return (
            f'<strong style="background-color: red; color: yellow;">⚠</strong>'
            f" <code>{escape(text)}</code>"
        )
