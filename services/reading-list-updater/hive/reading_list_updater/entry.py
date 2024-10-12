from __future__ import annotations

import json

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from hive.email import EmailMessage

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
        email = EmailMessage.from_bytes(data)
        return cls.from_email_summary(email.summary)

    @classmethod
    def from_email_summary(cls, email: dict[str, str]) -> ReadingListEntry:
        for header in ("to", "cc", "bcc"):
            if header in email:
                raise ValueError(header)

        body = email["body"].strip()
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

        if (title := email.get("subject")):
            title = title.strip()

        kwargs = {}
        if (date := email.get("date")):
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
