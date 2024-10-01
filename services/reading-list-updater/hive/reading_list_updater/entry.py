from __future__ import annotations

import email
import email.policy

from dataclasses import dataclass, field
from datetime import datetime
from email.message import EmailMessage
from typing import Optional


@dataclass
class ReadingListEntry:
    link: str
    title: Optional[str] = None
    notes: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

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
