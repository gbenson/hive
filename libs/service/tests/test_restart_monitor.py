import os

from hive.service import RestartMonitor, ServiceStatus


def test_init():
    class TestRestartMonitor(RestartMonitor):
        def __post_init__(self):
            pass

    got = TestRestartMonitor()
    assert got.name == "pytest"
    assert got.status == ServiceStatus.HEALTHY

    basenames = tuple(map(os.path.basename, got.filenames))
    assert basenames == (
        ".hive-service-restart.n-2.stamp",
        ".hive-service-restart.n-1.stamp",
        ".hive-service-restart.stamp",
        ".hive-service-restart.n+1.stamp",
    )
