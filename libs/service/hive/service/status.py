import os
import sys

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

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
