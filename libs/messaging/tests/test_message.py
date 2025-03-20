from datetime import datetime, timezone

import pytest

from cloudevents.abstract import CloudEvent
from pika.spec import Basic, BasicProperties

from hive.messaging import Message


class TestJSONCloudEventMessage:
    """A message that's a JSON-encoded CloudEvent.
    """
    @pytest.fixture
    def message(self) -> Message:
        return _build_test_message(
            content_type="application/cloudevents+json",
            message_body=(
                b'{"specversion":"1.0","id":"3a4a9760-c52d-495b-93a1-ad'
                b'f2acc7cdb0","source":"https://gbenson.net/hive/servic'
                b'es/matrix-connector","type":"net.gbenson.hive.service'
                b'_condition_report","datacontenttype":"application/jso'
                b'n","time":"2025-03-20T08:57:44.512454024Z","data":{"c'
                b'ondition":"healthy","messages":["Service restarted"]}}'
            ))

    def test_is_json(self, message: Message) -> None:
        assert message.is_json is True

    def test_json(self, message: Message) -> None:
        assert message.json() == {
            "specversion": "1.0",
            "id": "3a4a9760-c52d-495b-93a1-adf2acc7cdb0",
            "source": "https://gbenson.net/hive/services/matrix-connector",
            "type": "net.gbenson.hive.service_condition_report",
            "datacontenttype": "application/json",
            "time": "2025-03-20T08:57:44.512454024Z",
            "data": {
                "condition": "healthy",
                "messages": ["Service restarted"],
            }
        }

    def test_is_cloudevent(self, message: Message) -> None:
        assert message.is_cloudevent is True

    def test_event(self, message: Message) -> None:
        e = message.event()
        assert isinstance(e, CloudEvent)
        assert e.id == "3a4a9760-c52d-495b-93a1-adf2acc7cdb0"
        assert e.source == "https://gbenson.net/hive/services/matrix-connector"
        assert e.type == "net.gbenson.hive.service_condition_report"
        assert e.time == datetime(
            2025, 3, 20, 8, 57, 44, 512454,
            tzinfo=timezone.utc,
        )
        assert e.subject is None
        assert e.datacontenttype == "application/json"
        assert e.data == {
            "condition": "healthy",
            "messages": ["Service restarted"],
        }


class TestNonCloudEventJSONMessage:
    """An old-style (non-CloudEvent) JSON-encoded message.
    """
    @pytest.fixture
    def message(self) -> Message:
        return _build_test_message(
            content_type="application/json",
            message_body=(
                b'{"meta": {"timestamp": "2025-03-20 00:46:06.022723+00'
                b':00", "uuid": "fa849248-c97e-47f2-a269-d1cf2e8bf0d4",'
                b' "type": "service_status_report"}, "service": "hive-e'
                b'vent-vault", "condition": "HEALTHY", "messages": ["Se'
                b'rvice restarted"]}'
            ))

    def test_is_json(self, message: Message) -> None:
        assert message.is_json is True

    def test_json(self, message: Message) -> None:
        assert message.json() == {
            "meta": {
                "timestamp": "2025-03-20 00:46:06.022723+00:00",
                "uuid": "fa849248-c97e-47f2-a269-d1cf2e8bf0d4",
                "type": "service_status_report",
            },
            "service": "hive-event-vault",
            "condition": "HEALTHY",
            "messages": ["Service restarted"],
        }

    def test_is_cloudevent(self, message: Message) -> None:
        assert message.is_cloudevent is False

    def test_event(self, message: Message) -> None:
        with pytest.raises(ValueError) as excinfo:
            _ = message.event()
        assert repr(excinfo.value) == "ValueError('application/json')"


def _build_test_message(content_type: str, message_body: bytes) -> Message:
    props = BasicProperties(content_type=content_type)
    return Message(Basic.Deliver(), props, message_body)
