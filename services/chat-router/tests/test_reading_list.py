from datetime import datetime, timezone

import pytest

from hive.chat import ChatMessage

from hive.chat_router.handlers.reading_list import ReadingListUpdateHandler


@pytest.mark.parametrize(
    "body,expect_html",
    (("http://www.example.com",
      '<a href="http://www.example.com">http://www.example.com</a>'),
     ("https://example.com/foo?whatever=4#bar some quote",
      '<a href="https://example.com/foo?whatever=4#bar">'
      "https://example.com/foo?whatever=4#bar</a> some quote"),
     ))
def test_reading_list_update(mock_channel, body, expect_html):
    handler = ReadingListUpdateHandler()
    assert handler.handle(mock_channel, ChatMessage(
        text=body,
        sender="user",
        timestamp=datetime.fromtimestamp(1730071727.043, tz=timezone.utc),
        uuid="1c0a44e5-48ac-4464-b9ef-0117b11c2140",
    ))
    assert mock_channel.call_log == [(
        "publish_request", (), {
            "message": {
                "meta": {
                    "origin": {
                        "channel": "chat",
                        "message": {
                            "text": body,
                            "sender": "user",
                            "timestamp": "2024-10-27 23:28:47.043000+00:00",
                            "uuid": "1c0a44e5-48ac-4464-b9ef-0117b11c2140",
                        },
                    },
                },
                "date": "Sun, 27 Oct 2024 23:28:47 +0000",
                "body": body,
            },
            "routing_key": "readinglist.update.requests",
        },
    ), (
        "publish_event", (), {
            "message": {
                "text": body,
                "html": expect_html,
                "sender": "user",
                "timestamp": "2024-10-27 23:28:47.043000+00:00",
                "uuid": "1c0a44e5-48ac-4464-b9ef-0117b11c2140",
            },
            "routing_key": "chat.messages",
        },
    )]
