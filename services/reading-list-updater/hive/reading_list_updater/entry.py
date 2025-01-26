from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .wikitext import format_reading_list_entry


@dataclass
class ReadingListEntry:
    link: str
    title: Optional[str] = None
    notes: Optional[str] = None
    timestamp: str = field(default_factory=NotImplemented)

    def __post_init__(self):
        if not self.title:
            self.title = None
        if not self.notes:
            self.notes = None

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
            kwargs["timestamp"] = date

        return cls(link, title, notes, **kwargs)

    def as_wikitext(self):
        return format_reading_list_entry(
            timestamp=self.timestamp,
            link=self.link,
            title=self.title,
            notes=self.notes,
        )
