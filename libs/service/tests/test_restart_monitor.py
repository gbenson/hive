import os

from hive.service import RestartMonitor, ServiceCondition


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
