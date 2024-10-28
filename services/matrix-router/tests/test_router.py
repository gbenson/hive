import pytest

from hive.matrix_router.event import MatrixEvent
from hive.matrix_router.router import Router


class MockChannel:
    def __init__(self):
        self.published_requests = []

    def publish_request(self, *, mandatory, **kwargs):
        assert mandatory is True
        self.published_requests.append(kwargs)


class MockReactionManager:
    def start_story(self, *args, **kwargs):
        pass


@pytest.fixture
def channel():
    channel = MockChannel()
    channel.reaction_manager = MockReactionManager()
    yield channel


@pytest.mark.parametrize(
    "body",
    ("http://www.example.com",
     "https://example.com/foo?whatever=4#bar some quote",
     ))
def test_reading_list_update(channel, body):
    router = Router()
    router.on_matrix_event(channel, MatrixEvent({
        "source": {
            "type": "m.room.message",
            "content": {
                "msgtype": "m.text",
            },
        },
        "body": body,
        "event_id": "$26RqwJMLw-yds1GAH_QxjHRC1Da9oasK0e5VLnck_45",
        "server_timestamp": 1730071727043,
    }))
    assert channel.published_requests == [{
        "message": {
            "meta": {
                "origin": {
                    "channel": "matrix",
                    "event_id": "$26RqwJMLw-yds1GAH_QxjHRC1Da9oasK0e5VLnck_45",
                },
            },
            "date": "Sun, 27 Oct 2024 23:28:47 +0000",
            "body": body,
        },
        "routing_key": "readinglist.update.requests",
    }]