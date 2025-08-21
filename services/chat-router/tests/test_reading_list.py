import json

from pathlib import Path

from cloudevents.pydantic import CloudEvent

from pika.spec import BasicProperties

from hive.chat_router import Service
from hive.messaging import Message

RESOURCES = Path(__file__).parent / "resources" / "matrix.events"


def test_reading_list_update(mock_channel):
    message_path = RESOURCES / "share-link-multiline.json"
    message_json = message_path.read_bytes()
    message_dict = json.loads(message_json)
    expect_origin = CloudEvent.model_validate(message_dict)
    expect_body = expect_origin.data["content"]["body"]

    # sanity
    expect_lines = expect_body.split("\n")
    assert len(expect_lines) == 3
    assert expect_lines[0].startswith("https://pypi.org/project/gensim/ ")
    assert expect_lines[0].endswith(" prior to installing gensim.")
    assert expect_lines[1] == ""
    assert expect_lines[2].startswith("It is also recommended you ")
    assert expect_lines[2].endswith(" don’t need to do anything special.")

    # test
    Service().on_matrix_event(mock_channel, Message(
        method=None,
        properties=BasicProperties(
            content_type="application/cloudevents+json",
        ),
        body=message_json,
    ))

    assert len(mock_channel.call_log) == 2

    call = mock_channel.call_log[0]
    assert call.method == "publish_request"
    assert call.routing_key == "hive.matrix.requests"
    assert call.event.type == "net.gbenson.hive.matrix_user_typing_request"
    assert call.event.data == {"timeout": 5_000_000_000}

    call = mock_channel.call_log[1]
    assert call.method == "publish_request"
    assert call.routing_key == "hive.readinglist.update.requests"
    assert call.event.type == "net.gbenson.hive.readinglist_update_request"
    assert call.event.data == {
        "body": expect_body,
        "content_type": "text/plain",
        "created_from": {
            "id": "$Iv2XkxkQio3aU3CMcyss7eHWekMcqzpDEB15VZv-SlN",
            "source": "https://gbenson.net/hive/services/matrix-connector",
            "type": "net.gbenson.hive.matrix_event"
        },
    }
