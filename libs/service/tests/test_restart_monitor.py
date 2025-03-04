import os

from datetime import datetime

from hive.common import parse_uuid
from hive.service import RestartMonitor, ServiceCondition


class MockChannel:
    def maybe_publish_event(self, **kwargs):
        return kwargs


def test_init():
    class TestRestartMonitor(RestartMonitor):
        def __post_init__(self):
            pass

    got = TestRestartMonitor()
    assert got.status.service == "pytest"
    assert got.status.condition == ServiceCondition.HEALTHY

    basenames = tuple(map(os.path.basename, got.stamp_filenames))
    assert basenames == (
        ".hive-service-restart.n-2.stamp",
        ".hive-service-restart.n-1.stamp",
        ".hive-service-restart.stamp",
        ".hive-service-restart.n+1.stamp",
    )

    publish_kwargs = got.report_via_channel(MockChannel())
    assert publish_kwargs.keys() == {"routing_key", "message"}
    message = publish_kwargs["message"]
    assert message.keys() == {"service", "condition", "meta"}
    meta = message["meta"]
    assert meta.keys() == {"timestamp", "type", "uuid"}
    timestamp = datetime.fromisoformat(meta["timestamp"])
    uuid = parse_uuid(meta["uuid"])
    assert publish_kwargs == {
        "routing_key": "service.status",
        "message": {
            "meta": {
                "timestamp": str(timestamp),
                "type": "service_status_report",
                "uuid": str(uuid),
            },
            "service": "pytest",
            "condition": "HEALTHY",
        },
    }
