import pytest


class CallLogger:
    def __init__(self):
        self.call_log = []

    def __getattr__(self, attr):
        return MockMethod(attr, self.call_log)


class MockMethod:
    def __init__(self, name, call_log):
        self.name = name
        self.call_log = call_log

    def __call__(self, *args, **kwargs):
        self.call_log.append((self.name, args, kwargs))


@pytest.fixture
def mock_channel():
    return CallLogger()


@pytest.fixture
def mock_valkey():
    return CallLogger()
