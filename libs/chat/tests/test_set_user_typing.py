from hive.chat import set_user_typing
from hive.common.units import SECOND


def test_basic_operation(mock_messagebus, mock_channel):
    set_user_typing(23 * SECOND, channel=mock_channel)

    assert len(mock_messagebus.published_events) == 1
    event = mock_messagebus.published_events[0]
    assert event.type == "request"
    assert event.routing_key == "matrix.user.typing.requests"
    assert event.message is None
    assert event.cloudevent_data == {"timeout": 23_000_000_000}


def test_channel_creation(mock_messagebus):
    set_user_typing(False)

    assert len(mock_messagebus.published_events) == 1
    event = mock_messagebus.published_events[0]
    assert event.type == "request"
    assert event.routing_key == "matrix.user.typing.requests"
    assert event.message is None
    assert event.cloudevent_data == {"timeout": 0}
