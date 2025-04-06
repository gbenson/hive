from datetime import datetime, timezone

import pytest

from cloudevents.pydantic import CloudEvent

from hive.chat_router import Service


@pytest.mark.parametrize(
    "body,expect_html",
    (("http://www.example.com",
      '<a href="http://www.example.com">http://www.example.com</a>'),
     ("https://example.com/foo?whatever=4#bar some quote",
      '<a href="https://example.com/foo?whatever=4#bar">'
      "https://example.com/foo?whatever=4#bar</a> some quote"),
     ))
def test_reading_list_update(mock_channel, body, expect_html):
    Service().on_user_input(mock_channel, CloudEvent({
        "id": "1c0a44e5-48ac-4464-b9ef-0117b11c2140",
        "source": "reading_list_update_test_source",
        "type": "reading_list_update_test_type",
        "time": datetime.fromtimestamp(1730071727.043, tz=timezone.utc),
    }), body)

    assert len(mock_channel.call_log) == 1
    _, _, kwargs = mock_channel.call_log[0]
    origin = kwargs["message"]["meta"]["origin"]["message"]
    assert origin["id"] == "1c0a44e5-48ac-4464-b9ef-0117b11c2140"
    assert origin["source"] == "reading_list_update_test_source"
    assert origin["type"] == "reading_list_update_test_type"
    assert origin["time"] == "2024-10-27T23:28:47.043000+00:00"
    assert mock_channel.call_log == [(
        "publish_request", (), {
            "message": {
                "meta": {
                    "origin": {
                        "channel": "matrix",
                        "message": origin,
                    },
                },
                "date": "Sun, 27 Oct 2024 23:28:47 +0000",
                "body": body,
            },
            "routing_key": "readinglist.update.requests",
        },
    )]
