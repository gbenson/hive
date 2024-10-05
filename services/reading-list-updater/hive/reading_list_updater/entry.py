from __future__ import annotations

import email
import email.policy
import json

from dataclasses import dataclass, field
from datetime import datetime
from email.message import EmailMessage
from typing import Any, Optional

from .wikitext import format_reading_list_entry


@dataclass
class ReadingListEntry:
    link: str
    title: Optional[str] = None
    notes: Optional[str] = None
    timestamp: str | datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.title:
            self.title = None
        if not self.notes:
            self.notes = None
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)

    @classmethod
    def from_email_bytes(cls, data: bytes) -> ReadingListEntry:
        return cls.from_email_message(email.message_from_bytes(
            data, policy=email.policy.default))

    @classmethod
    def from_email_message(cls, email: EmailMessage) -> ReadingListEntry:
        for header in ("To", "Cc", "Bcc"):
            if email[header]:
                raise ValueError(header)

        body = email.get_body(("plain",))
        if body is None:
            raise ValueError
        body = body.get_content().strip()
        if not body:
            raise ValueError

        body_parts = body.split(maxsplit=1)
        if len(body_parts) == 1:
            body_parts.append(None)
        link, notes = body_parts
        if link.startswith("<") and link.endswith(">"):
            link = link[1:-1]
        if not link:
            raise ValueError

        title = email["Subject"]
        if title is not None:
            title = title.strip()

        kwargs = {}
        date = email["Date"]
        if date:
            kwargs["timestamp"] = date.datetime

        return cls(link, title, notes, **kwargs)

    def as_dict(self) -> dict[str]:
        report = {
            "meta": {
                "timestamp": str(self.timestamp),
                "type": "reading_list_entry",
            },
            "link": self.link,
        }
        if self.title:
            report["title"] = self.title
        if self.notes:
            report["notes"] = self.notes
        return report

    @classmethod
    def from_json_bytes(cls, data: bytes) -> ReadingListEntry:
        return cls.from_dict(json.loads(data))

    @classmethod
    def from_dict(cls, report: dict[str, Any]) -> ReadingListEntry:
        report = report.copy()
        meta = report.pop("meta")
        report["timestamp"] = meta["timestamp"]
        return cls(**report)

    def as_wikitext(self):
        return format_reading_list_entry(
            timestamp=self.timestamp,
            link=self.link,
            title=self.title,
            notes=self.notes,
        )
