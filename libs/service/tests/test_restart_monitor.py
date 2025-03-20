import os

from cloudevents.abstract import CloudEvent

from hive.common import parse_uuid, utc_now
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
        ".hive-service-restart.n-1.stamp",
        ".hive-service-restart.stamp",
        ".hive-service-restart.n+1.stamp",
    )

    publish_kwargs = got.report_via_channel(MockChannel())
    assert publish_kwargs.keys() == {"routing_key", "message"}
    assert publish_kwargs["routing_key"] == "service.status.reports"
    e = publish_kwargs["message"]
    assert isinstance(e, CloudEvent)

    _ = parse_uuid(e.id)
    assert e.source == "https://gbenson.net/hive/services/pytest"
    assert e.type == "net.gbenson.hive.service_status_report"
    assert 0 < (utc_now() - e.time).total_seconds() < 1
    assert e.subject == "pytest"
    assert e.data == {
        "condition": "healthy",
    }
