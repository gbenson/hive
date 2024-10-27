import json
import os

import pytest

from hive.matrix_router.event import MatrixEvent
from hive.matrix_router.router import Router


def serialized_event_filenames():
    testdir = os.path.dirname(__file__)
    for dirpath, dirnames, filenames in os.walk(testdir):
        for filepath in sorted(
                os.path.join(dirpath, filename)
                for filename in filenames
                if filename.endswith(".json")):
            yield filepath


@pytest.mark.parametrize("filename", serialized_event_filenames())
def test_smoke(filename):
    router = Router()
    with open(filename) as fp:
        event = MatrixEvent(json.load(fp))

    assert event.event_id == event._event._event["event_id"]
    assert event.timestamp_ms == event._event._event["origin_server_ts"]
    assert event.room_id == event._event._event["room_id"]
    assert event.body == event.content._content["body"]

    router.on_matrix_event(MockChannel(), event)


class MockChannel:
    def publish_request(self, **kwargs):
        for key, value in kwargs.items():
            print(f"{key:12}: {value!r}")
