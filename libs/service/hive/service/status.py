import os
import sys

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from hive.messaging import Channel

ServiceCondition = Enum("ServiceCondition", "HEALTHY DUBIOUS IN_ERROR")


@dataclass
class ServiceStatus:
    try:
        DEFAULT_SERVICE = os.path.basename(sys.argv[0])
        DEFAULT_INITIAL_CONDITION = ServiceCondition.HEALTHY
    except Exception as e:
        DEFAULT_SERVICE = f"[ERROR: {e}]"
        DEFAULT_INITIAL_CONDITION = ServiceCondition.DUBIOUS

    service: str = DEFAULT_SERVICE
    condition: ServiceCondition = DEFAULT_INITIAL_CONDITION
    messages: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    _uuid: UUID = field(default_factory=uuid4)

    def _as_dict(self) -> dict[str]:
        report = {
            "meta": {
                "timestamp": str(self.timestamp),
                "uuid": str(self._uuid),
                "type": "service_status_report",
            },
            "service": self.service,
            "condition": self.condition.name,
        }
        if self.messages:
            report["messages"] = self.messages[:]
        return report

    def report_via_channel(
            self,
            channel: Channel,
            *,
            routing_key: str = "service.status",
            mandatory: bool = False,
    ):
        """Publish this report via a :class:`hive.messaging.Channel`.
        """
        return channel.publish_event(
            message=self._as_dict(),
            routing_key=routing_key,
            mandatory=mandatory,
        )
