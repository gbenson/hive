import os
import sys

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from cloudevents.pydantic import CloudEvent

from hive.common import utc_now
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
    timestamp: datetime = field(default_factory=utc_now)
    _uuid: UUID = field(default_factory=uuid4)

    def _as_event(self) -> CloudEvent:
        data = {"condition": self.condition.name.lower()}
        if self.messages:
            data["messages"] = self.messages[:]

        return CloudEvent(
            id=str(self._uuid),
            source=f"https://gbenson.net/hive/services/{self.service}",
            type="net.gbenson.hive.service_status_report",
            time=self.timestamp,
            subject=self.service,
            data=data,
        )

    def report_via_channel(
            self,
            channel: Channel,
            *,
            routing_key: str = "service.status.reports",
    ):
        """Publish this report via a :class:`hive.messaging.Channel`.
        """
        return channel.maybe_publish_event(
            message=self._as_event(),
            routing_key=routing_key,
        )
