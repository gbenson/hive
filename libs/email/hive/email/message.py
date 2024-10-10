from __future__ import annotations

import logging

from email import message_from_binary_file, message_from_bytes
from email.message import EmailMessage
from email.policy import compat32, default
from functools import cached_property
from typing import BinaryIO, Optional

from html2text import html2text

logger = logging.getLogger(__name__)


class Message(EmailMessage):
    @classmethod
    def from_file(cls, fp: BinaryIO) -> Message:
        """Deserialize an email from a file-like object."""
        return cls._deserialize(message_from_binary_file, fp)

    @classmethod
    def from_bytes(cls, s: bytes | bytearray) -> Message:
        """Deserialize an email from a sequence of bytes.
        """
        return cls._deserialize(message_from_bytes, s)

    @classmethod
    def _deserialize(cls, deserializer, deserializable) -> Message:
        return deserializer(
            deserializable,
            _class=cls,
            policy=default,
        )

    @cached_property
    def date(self) -> Optional[str]:
        return self.get("Date")

    @cached_property
    def _from(self) -> Optional[str]:
        return self.get("From")

    @cached_property
    def to(self) -> Optional[str]:
        return self.get("To")

    @cached_property
    def cc(self) -> Optional[str]:
        return self.get("Cc")

    @cached_property
    def bcc(self) -> Optional[str]:
        return self.get("Bcc")

    @cached_property
    def subject(self) -> Optional[str]:
        return self.get("Subject")

    @cached_property
    def delivered_to(self) -> Optional[str]:
        return self.get("X-Original-To", "").lower() or None

    # Using compat32 allows these to be whatever they are.
    # (default requires the same form as email addresses)
    @cached_property
    def message_id(self) -> Optional[str]:
        for k, v in self._headers:
            if k.lower() == "message-id":
                return compat32.header_fetch_parse(k, v)
        return None

    _SUMMARY_HEADER_ATTRS = [
        "date",
        "_from",
        "to",
        "cc",
        "bcc",
        "subject",
        "message_id",
        "delivered_to",
    ]

    @property
    def summary_headers(self) -> dict[str, str]:
        return dict(
            (name.lstrip("_"), value)
            for name, value in (
                    (attr, getattr(self, attr))
                    for attr in self._SUMMARY_HEADER_ATTRS
            )
            if value
        )

    @property
    def summary(self) -> dict[str, str]:
        result = self.summary_headers
        if (body := self.plain_content):
            result["body"] = body
        return result

    # What content types to expect?
    #
    # From <https://stackoverflow.com/questions/3902455/
    #   mail-multipart-alternative-vs-multipart-mixed#23853079>,
    #
    # If your requirement is an email with:
    #  - text and html versions
    #  - html version has embedded (inline) images
    #  - attachments
    #
    # The only structure I found that works with Gmail/Outlook/iPad is:
    #
    # mixed
    #  - alternative
    #      - text
    #      - related
    #          - html
    #          - inline image
    #          - inline image
    #  - attachment
    #  - attachment

    @cached_property
    def content_type(self) -> str:
        return self.get_content_type()

    @cached_property
    def filename(self) -> Optional[str]:
        return self.get_filename()

    # This fixes self.get_content() when the charset param is empty
    # (i.e. 'Content-Type: text/plain; charset=""')
    def get_param(self, *args, **kwargs):
        result = super().get_param(*args, **kwargs)
        if result or kwargs or args != ("charset", "ASCII"):
            return result
        return "ASCII"

    @cached_property
    def plain_body(self) -> Optional[Message]:
        """The MIME part that is the best candidate to be the
        plain text "body" of this message.
        """
        return self.get_body(("plain",))

    @cached_property
    def plain_content(self) -> str:
        """A plain text version of the main body of the message
        (i.e. the part which isn't attachments).  This could be
        verbatim from a text/plain MIME part or transformed from
        a text/html one.
        """
        if (plain_body := self.plain_body):
            if plain_body.content_type == "text/plain":
                if (plain_content := plain_body.get_content()):
                    if (result := self._normspace(plain_content)):
                        return result

        if (html_content := self.html_content):
            if (plain_content := html2text(html_content)):
                if (result := self._normspace(plain_content)):
                    return result

        return ""

    @staticmethod
    def _normspace(text: str) -> str:
        """Remove useless whitespace.
        """
        return "\n".join(
            line.rstrip()
            for line in text.strip().split("\n")
        )

    @cached_property
    def html_body(self) -> Optional[Message]:
        """The MIME part that is the best candidate to be the
        HTML "body" of this message.
        """
        if not (preferred_body := self.get_body()):
            return None
        if preferred_body is self.plain_body:
            return None
        match preferred_body.content_type:
            case "text/html":
                return preferred_body
            case "multipart/related":
                return preferred_body.get_body(("html",))
            case unhandled:  # pragma: no cover
                logger.warning(
                    "%s: unhandled HTML body type",
                    unhandled,
                )
                return None

    @cached_property
    def html_content(self) -> Optional[str]:
        """The HTML variant of the main body of the message,
        or None if no HTML variant exists.
        """
        if not (html_body := self.html_body):
            return None
        if html_body.content_type != "text/html":  # pragma: no cover
            logger.warning(
                "%s: unhandled HTML content type",
                html_body.content_type,
            )
            return None
        if not (html_content := html_body.get_content().strip()):
            return None
        return html_content

    @cached_property
    def pdf_attachments(self) -> list[Message]:
        return [
            attachment
            for attachment in self.iter_attachments()
            if attachment.is_pdf
        ]

    @cached_property
    def is_pdf(self):
        if self.content_type == "application/pdf":
            return True
        if self.content_type != "application/octet-stream":
            return False
        if not self.filename:  # pragma: no cover
            return False
        return self.filename.lower().endswith(".pdf")

    @cached_property
    def pdf_content(self) -> Optional[bytes]:
        if not self.is_pdf:
            return None
        return self.get_content()
