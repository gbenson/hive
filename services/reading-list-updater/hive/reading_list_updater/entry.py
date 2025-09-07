from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from .url_rewriters import maybe_rewrite_url
from .wikitext import format_reading_list_entry


@dataclass
class ReadingListEntry:
    url: str
    title: Optional[str] = None
    notes: Optional[str] = None
    timestamp: str = field(default_factory=NotImplemented)
    source: Optional[dict[str, Any]] = None

    def __post_init__(self):
        if not self.title:
            self.title = None
        if not self.notes:
            self.notes = None
        self.url = maybe_rewrite_url(self.url)

    @classmethod
    def from_email_summary(cls, email: dict[str, str]) -> ReadingListEntry:
        for header in ("to", "cc", "bcc"):
            if header in email:
                raise ValueError(header)

        body = email["body"].strip()
        if not body:
            raise ValueError

        if body.startswith("<"):
            body = body[1:].replace(">", "", 1)

        body_parts = body.split(maxsplit=1)
        if len(body_parts) == 1:
            body_parts.append(None)
        url, notes = body_parts
        if not url:
            raise ValueError

        if (title := email.get("subject")):
            title = title.strip()

        kwargs = {}
        if (date := email.get("date")):
            kwargs["timestamp"] = date
        if (source := email.get("created_from")):
            kwargs["source"] = source.copy()

        return cls(url, title, notes, **kwargs)

    @property
    def source_matrix_event_id(self) -> Optional[str]:
        if not (source := self.source):
            return None
        if source.get("type") != "net.gbenson.hive.matrix_event":
            return None
        return source.get("id")

    def as_wikitext(self):
        return format_reading_list_entry(
            timestamp=self.timestamp,
            url=self.url,
            title=self.title,
            notes=self.notes,
        )

    def json(self) -> dict[str, Any]:
        return dict(
            (key, value)
            for key, value in asdict(self).items()
            if value
        )
