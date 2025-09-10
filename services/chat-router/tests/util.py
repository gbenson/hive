from datetime import datetime
from typing import Optional
from unittest.mock import Mock

from hive.common import parse_datetime

from hive.chat_router.request import Request


def make_test_request(text: str, time: Optional[datetime] = None) -> Request:
    if not time:
        time = parse_datetime("2024-09-02 11:10:31.186283Z")
    return Mock(text=text, time=time)
