from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import RFC_4122, UUID, uuid4


@dataclass
class ChatMessage:
    text: Optional[str] = None
    html: Optional[str] = None
    sender: str = "hive"
    timestamp: str | datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc))
    uuid: str | UUID = field(default_factory=uuid4)

    def __post_init__(self):
        if not self.text and not self.html:
            raise ValueError

        if not isinstance(self.timestamp, datetime):
            self.timestamp = datetime.fromisoformat(self.timestamp)

        if not isinstance(self.uuid, UUID):
            self.uuid = UUID(self.uuid)

        if self.uuid.variant != RFC_4122:
            raise ValueError(self.uuid)
        if self.uuid.version != 4:
            raise ValueError(self.uuid)

    def json(self) -> dict[str, Any]:
        attrs = (field.name for field in fields(self))
        items = ((attr, getattr(self, attr)) for attr in attrs)
        return dict((key, str(value)) for key, value in items if value)
