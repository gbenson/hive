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

    assert event.event_id == event._decorated_event["event_id"]
    if event.event_type != "m.room.redaction":
        event.room_id == event._decorated_event["room_id"]
        assert event.body == event.content._content["body"]

    router.on_matrix_event(MockChannel(), event)


class MockChannel:
    @property
    def reaction_manager(self):
        return MockReactionManager()

    def publish_request(self, **kwargs):
        for key, value in kwargs.items():
            print(f"{key:12}: {value!r}")

    def publish_event(self, *, routing_key, message):
        assert routing_key == "chat.messages"


class MockReactionManager:
    def start_story(self, *args, **kwargs):
        pass
