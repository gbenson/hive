import json
import time

from datetime import datetime, timedelta, timezone

import pytest

from cloudevents.pydantic import CloudEvent
from pika import BasicProperties, DeliveryMode

from hive.common import parse_datetime, parse_uuid
from hive.messaging import Channel, Message


class MockPika:
    def __getattr__(self, attr):
        if attr == "_prefetch_count":
            raise AttributeError(attr)
        raise NotImplementedError(attr)


class MockMethod:
    def __init__(self, *, returns=None):
        self.call_log = []
        self._returns = returns

    def __call__(self, *args, **kwargs):
        time.sleep(0.01)
        self.call_log.append((args, kwargs))
        return self._returns


class MockCallback(MockMethod):
    def __call__(self, channel: Channel, message: Message):
        return super().__call__(channel, message)


expect_properties = BasicProperties(
    content_type="application/json",
    delivery_mode=DeliveryMode.Persistent,
)


def test_publish_request():
    mock = MockPika()
    mock.exchange_declare = MockMethod()
    mock.basic_publish = MockMethod()

    channel = Channel(pika=mock)
    channel.publish_request(
        message={
            "bonjour": "madame",
        },
        routing_key="egg.nog",
    )

    assert mock.exchange_declare.call_log == [((), {
        "exchange": "hive.egg.nog",
        "exchange_type": "fanout",
        "durable": True,
    })]
    assert mock.basic_publish.call_log == [((), {
        "exchange": "hive.egg.nog",
        "routing_key": "",
        "body": b'{"bonjour": "madame"}',
        "properties": expect_properties,
        "mandatory": True,
    })]


@pytest.mark.parametrize(
    "channel_kwargs",
    ({},
     {"name": "hello.world"},
     ))
def test_consume_requests(channel_kwargs):
    mock = MockPika()
    mock.exchange_declare = MockMethod()
    mock.basic_qos = MockMethod()
    mock.queue_declare = MockMethod(
        returns=type("Result", (), dict(
            method=type("Method", (), dict(
                queue="TeStQuEu3")))))
    mock.queue_bind = MockMethod()
    mock.basic_consume = MockMethod()
    on_message_callback = MockCallback()
    mock.basic_ack = MockMethod()

    channel = Channel(pika=mock, **channel_kwargs)
    channel.consume_requests(
        queue="arr.pirates",
        on_message_callback=on_message_callback,
    )

    assert mock.exchange_declare.call_log == [((), {
        "exchange": "hive.arr.pirates",
        "exchange_type": "fanout",
        "durable": True,
    }), ((), {
        "exchange": "hive.dead.letter",
        "exchange_type": "direct",
        "durable": True,
    })]
    assert mock.basic_qos.call_log == [((), {
        "prefetch_count": 1,
    })]
    assert mock.queue_declare.call_log == [((
        "x.arr.pirates",
    ), {
        "durable": True,
    }), ((
        "arr.pirates",
    ), {
        "durable": True,
        "arguments": {
            "x-dead-letter-exchange": "hive.dead.letter",
        },
    })]
    assert mock.queue_bind.call_log == [((), {
        "queue": "x.arr.pirates",
        "exchange": "hive.dead.letter",
        "routing_key": "arr.pirates",
    }), ((), {
        "queue": "arr.pirates",
        "exchange": "hive.arr.pirates",
    })]

    assert len(mock.basic_consume.call_log) == 1
    assert len(mock.basic_consume.call_log[0]) == 2
    got_callback = mock.basic_consume.call_log[0][1]["on_message_callback"]
    assert mock.basic_consume.call_log == [((), {
        "queue": "arr.pirates",
        "on_message_callback": got_callback,
    })]
    assert on_message_callback.call_log == []
    assert mock.basic_ack.call_log == []

    expect_method = type("method", (), {"delivery_tag": 5})
    expect_body = b'{"hello":"W0RLD"}'
    got_callback(channel._pika, expect_method, expect_properties, expect_body)

    assert len(on_message_callback.call_log) == 1
    assert len(on_message_callback.call_log[0]) == 2
    assert len(on_message_callback.call_log[0][0]) == 2
    message = on_message_callback.call_log[0][0][1]
    assert on_message_callback.call_log == [((channel, message), {})]
    assert message.method is expect_method
    assert message.properties is expect_properties
    assert message.body is expect_body

    assert mock.basic_ack.call_log == [((), {"delivery_tag": 5})]


def test_publish_event():
    mock = MockPika()
    mock.exchange_declare = MockMethod()
    mock.basic_publish = MockMethod()

    channel = Channel(pika=mock)
    channel.publish_event(
        message={
            "bonjour": "madame",
        },
        routing_key="egg.nog",
    )

    assert mock.exchange_declare.call_log == [((), {
        "exchange": "hive.egg.nog",
        "exchange_type": "fanout",
        "durable": True,
    })]
    assert mock.basic_publish.call_log == [((), {
        "exchange": "hive.egg.nog",
        "routing_key": "",
        "body": b'{"bonjour": "madame"}',
        "properties": expect_properties,
        "mandatory": False,
    })]


def test_consume_events():
    mock = MockPika()
    mock.exchange_declare = MockMethod()
    mock.basic_qos = MockMethod()
    mock.queue_declare = MockMethod(
        returns=type("Result", (), dict(
            method=type("Method", (), dict(
                queue="TeStQuEu3")))))
    mock.queue_bind = MockMethod()
    mock.basic_consume = MockMethod()
    on_message_callback = MockCallback()
    mock.basic_ack = MockMethod()

    channel = Channel(pika=mock)
    channel.consume_events(
        queue="arr.pirates",
        on_message_callback=on_message_callback,
    )

    assert mock.exchange_declare.call_log == [((), {
        "exchange": "hive.arr.pirates",
        "exchange_type": "fanout",
        "durable": True,
    }), ((), {
        "exchange": "hive.dead.letter",
        "exchange_type": "direct",
        "durable": True,
    })]
    assert mock.basic_qos.call_log == [((), {
        "prefetch_count": 1,
    })]
    assert mock.queue_declare.call_log == [((
        "x.pytest.arr.pirates",
    ), {
        "durable": True,
    }), ((
        "pytest.arr.pirates",
    ), {
        "durable": True,
        "arguments": {
            "x-dead-letter-exchange": "hive.dead.letter",
        },
    })]
    assert mock.queue_bind.call_log == [((), {
        "queue": "x.pytest.arr.pirates",
        "exchange": "hive.dead.letter",
        "routing_key": "pytest.arr.pirates",
    }), ((), {
        "exchange": "hive.arr.pirates",
        "queue": "pytest.arr.pirates",
    })]

    assert len(mock.basic_consume.call_log) == 1
    assert len(mock.basic_consume.call_log[0]) == 2
    got_callback = mock.basic_consume.call_log[0][1]["on_message_callback"]
    assert mock.basic_consume.call_log == [((), {
        "queue": "pytest.arr.pirates",
        "on_message_callback": got_callback,
    })]
    assert on_message_callback.call_log == []
    assert mock.basic_ack.call_log == []

    expect_method = type("method", (), {"delivery_tag": 5})
    expect_body = b'{"hello":"W0RLD"}'
    got_callback(channel._pika, expect_method, expect_properties, expect_body)

    assert len(on_message_callback.call_log) == 1
    assert len(on_message_callback.call_log[0]) == 2
    assert len(on_message_callback.call_log[0][0]) == 2
    message = on_message_callback.call_log[0][0][1]
    assert on_message_callback.call_log == [((channel, message), {})]
    assert message.method is expect_method
    assert message.properties is expect_properties
    assert message.body is expect_body

    assert mock.basic_ack.call_log == [((), {"delivery_tag": 5})]


def test_publish_with_expiration():
    mock = MockPika()
    mock.exchange_declare = MockMethod()
    mock.basic_publish = MockMethod()

    channel = Channel(pika=mock)
    channel.publish_request(
        message={
            "bonjour": "madame",
        },
        routing_key="egg.nog",
        consume_by=datetime.now(tz=timezone.utc) + timedelta(seconds=1),
    )

    assert len(mock.basic_publish.call_log) == 1
    got_properties = mock.basic_publish.call_log[0][1]["properties"]
    expiration = got_properties.expiration
    assert isinstance(expiration, str)
    assert 0 < int(expiration) < 1000

    got_properties.expiration = None
    assert mock.exchange_declare.call_log == [((), {
        "exchange": "hive.egg.nog",
        "exchange_type": "fanout",
        "durable": True,
    })]
    assert mock.basic_publish.call_log == [((), {
        "exchange": "hive.egg.nog",
        "routing_key": "",
        "body": b'{"bonjour": "madame"}',
        "properties": expect_properties,
        "mandatory": True,
    })]


def test_named_channel():
    mock = MockPika()
    mock.exchange_declare = MockMethod()
    mock.basic_qos = MockMethod()
    mock.queue_declare = MockMethod(
        returns=type("Result", (), dict(
            method=type("Method", (), dict(
                queue="TeStQuEu3")))))
    mock.queue_bind = MockMethod()
    mock.basic_consume = MockMethod()
    on_message_callback = MockCallback()
    mock.basic_ack = MockMethod()

    channel = Channel(pika=mock, name="Eugene.Goostman")
    channel.consume_events(
        queue="arr.pirates",
        on_message_callback=on_message_callback,
    )

    assert mock.exchange_declare.call_log == [((), {
        "exchange": "hive.arr.pirates",
        "exchange_type": "fanout",
        "durable": True,
    }), ((), {
        "exchange": "hive.dead.letter",
        "exchange_type": "direct",
        "durable": True,
    })]
    assert mock.basic_qos.call_log == [((), {
        "prefetch_count": 1,
    })]
    assert mock.queue_declare.call_log == [((
        "x.pytest.Eugene.Goostman.arr.pirates",
    ), {
        "durable": True,
    }), ((
        "pytest.Eugene.Goostman.arr.pirates",
    ), {
        "durable": True,
        "arguments": {
            "x-dead-letter-exchange": "hive.dead.letter",
        },
    })]
    assert mock.queue_bind.call_log == [((), {
        "queue": "x.pytest.Eugene.Goostman.arr.pirates",
        "exchange": "hive.dead.letter",
        "routing_key": "pytest.Eugene.Goostman.arr.pirates",
    }), ((), {
        "exchange": "hive.arr.pirates",
        "queue": "pytest.Eugene.Goostman.arr.pirates",
    })]

    assert len(mock.basic_consume.call_log) == 1
    assert len(mock.basic_consume.call_log[0]) == 2
    got_callback = mock.basic_consume.call_log[0][1]["on_message_callback"]
    assert mock.basic_consume.call_log == [((), {
        "queue": "pytest.Eugene.Goostman.arr.pirates",
        "on_message_callback": got_callback,
    })]
    assert on_message_callback.call_log == []
    assert mock.basic_ack.call_log == []

    expect_method = type("method", (), {"delivery_tag": 5})
    expect_body = b'{"hello":"W0RLD"}'
    got_callback(channel._pika, expect_method, expect_properties, expect_body)

    assert len(on_message_callback.call_log) == 1
    assert len(on_message_callback.call_log[0]) == 2
    assert len(on_message_callback.call_log[0][0]) == 2
    message = on_message_callback.call_log[0][0][1]
    assert on_message_callback.call_log == [((channel, message), {})]
    assert message.method is expect_method
    assert message.properties is expect_properties
    assert message.body is expect_body

    assert mock.basic_ack.call_log == [((), {"delivery_tag": 5})]


def test_consume_exclusive():
    mock = MockPika()
    mock.exchange_declare = MockMethod()
    mock.basic_qos = MockMethod()
    mock.queue_declare = MockMethod(
        returns=type("Result", (), dict(
            method=type("Method", (), dict(
                queue="TeStQuEu3")))))
    mock.queue_bind = MockMethod()
    mock.basic_consume = MockMethod()
    on_message_callback = MockCallback()
    mock.basic_ack = MockMethod()

    channel = Channel(pika=mock)
    channel.consume_events(
        queue="arr.pirates",
        on_message_callback=on_message_callback,
        exclusive=True,
    )

    assert mock.exchange_declare.call_log == [((), {
        "exchange": "hive.arr.pirates",
        "exchange_type": "fanout",
        "durable": True,
    })]
    assert mock.basic_qos.call_log == [((), {
        "prefetch_count": 1,
    })]
    assert mock.queue_declare.call_log == [((
        "pytest.arr.pirates",
    ), {
        "exclusive": True,
    })]
    assert mock.queue_bind.call_log == [((), {
        "exchange": "hive.arr.pirates",
        "queue": "pytest.arr.pirates",
    })]

    assert len(mock.basic_consume.call_log) == 1
    assert len(mock.basic_consume.call_log[0]) == 2
    got_callback = mock.basic_consume.call_log[0][1]["on_message_callback"]
    assert mock.basic_consume.call_log == [((), {
        "queue": "pytest.arr.pirates",
        "on_message_callback": got_callback,
    })]
    assert on_message_callback.call_log == []
    assert mock.basic_ack.call_log == []

    expect_method = type("method", (), {"delivery_tag": 5})
    expect_body = b'{"hello":"W0RLD"}'
    got_callback(channel._pika, expect_method, expect_properties, expect_body)

    assert len(on_message_callback.call_log) == 1
    assert len(on_message_callback.call_log[0]) == 2
    assert len(on_message_callback.call_log[0][0]) == 2
    message = on_message_callback.call_log[0][0][1]
    assert on_message_callback.call_log == [((channel, message), {})]
    assert message.method is expect_method
    assert message.properties is expect_properties
    assert message.body is expect_body

    assert mock.basic_ack.call_log == [((), {"delivery_tag": 5})]


def test_publish_topic():
    mock = MockPika()
    mock.exchange_declare = MockMethod()
    mock.basic_publish = MockMethod()

    channel = Channel(pika=mock)
    channel.publish_event(
        message={
            "bonjour": "madame",
        },
        routing_key="egg.nog",
        topic="recipes",
    )

    assert mock.exchange_declare.call_log == [((), {
        "exchange": "hive.egg.nog",
        "exchange_type": "topic",
        "durable": True,
    })]
    assert mock.basic_publish.call_log == [((), {
        "exchange": "hive.egg.nog",
        "routing_key": "recipes",
        "body": b'{"bonjour": "madame"}',
        "properties": expect_properties,
        "mandatory": False,
    })]


def test_consume_topic():
    mock = MockPika()
    mock.exchange_declare = MockMethod()
    mock.basic_qos = MockMethod()
    mock.queue_declare = MockMethod(
        returns=type("Result", (), dict(
            method=type("Method", (), dict(
                queue="TeStQuEu3")))))
    mock.queue_bind = MockMethod()
    mock.basic_consume = MockMethod()
    on_message_callback = MockCallback()
    mock.basic_ack = MockMethod()

    channel = Channel(pika=mock)
    channel.consume_events(
        queue="arr.pirates",
        on_message_callback=on_message_callback,
        topic="booty",
    )

    assert mock.exchange_declare.call_log == [((), {
        "exchange": "hive.arr.pirates",
        "exchange_type": "topic",
        "durable": True,
    }), ((), {
        "exchange": "hive.dead.letter",
        "exchange_type": "direct",
        "durable": True,
    })]
    assert mock.basic_qos.call_log == [((), {
        "prefetch_count": 1,
    })]
    assert mock.queue_declare.call_log == [((
        "x.pytest.arr.pirates",
    ), {
        "durable": True,
    }), ((
        "pytest.arr.pirates",
    ), {
        "durable": True,
        "arguments": {
            "x-dead-letter-exchange": "hive.dead.letter",
        },
    })]
    assert mock.queue_bind.call_log == [((), {
        "queue": "x.pytest.arr.pirates",
        "exchange": "hive.dead.letter",
        "routing_key": "pytest.arr.pirates",
    }), ((), {
        "exchange": "hive.arr.pirates",
        "queue": "pytest.arr.pirates",
        "routing_key": "booty",
    })]

    assert len(mock.basic_consume.call_log) == 1
    assert len(mock.basic_consume.call_log[0]) == 2
    got_callback = mock.basic_consume.call_log[0][1]["on_message_callback"]
    assert mock.basic_consume.call_log == [((), {
        "queue": "pytest.arr.pirates",
        "on_message_callback": got_callback,
    })]
    assert on_message_callback.call_log == []
    assert mock.basic_ack.call_log == []

    expect_method = type("method", (), {"delivery_tag": 5})
    expect_body = b'{"hello":"W0RLD"}'
    got_callback(channel._pika, expect_method, expect_properties, expect_body)

    assert len(on_message_callback.call_log) == 1
    assert len(on_message_callback.call_log[0]) == 2
    assert len(on_message_callback.call_log[0][0]) == 2
    message = on_message_callback.call_log[0][0][1]
    assert on_message_callback.call_log == [((channel, message), {})]
    assert message.method is expect_method
    assert message.properties is expect_properties
    assert message.body is expect_body

    assert mock.basic_ack.call_log == [((), {"delivery_tag": 5})]


def test_publish_cloudevents_event():
    mock = MockPika()
    mock.exchange_declare = MockMethod()
    mock.basic_publish = MockMethod()

    channel = Channel(pika=mock)
    channel.publish_event(
        message=CloudEvent(
            id="VeRyUn1qU3Me5sAgEiD",
            source="https://gbenson.net/hive/libs/messaging/test",
            type="net.gbenson.hive.test_event",
            data={"bonjour": "madame"},
            time=datetime(2025, 3, 20, 8, 57, 44, 512454, tzinfo=timezone.utc),
        ),
        routing_key="egg.nog",
    )

    assert mock.exchange_declare.call_log == [((), {
        "exchange": "hive.egg.nog",
        "exchange_type": "fanout",
        "durable": True,
    })]

    assert len(mock.basic_publish.call_log) == 1
    body = mock.basic_publish.call_log[0][1]["body"]
    assert isinstance(body, bytes)
    assert mock.basic_publish.call_log == [((), {
        "exchange": "hive.egg.nog",
        "routing_key": "",
        "body": body,
        "properties": BasicProperties(
            content_type="application/cloudevents+json",
            delivery_mode=DeliveryMode.Persistent,
        ),
        "mandatory": False,
    })]
    assert json.loads(body) == {
        "specversion": "1.0",
        "id": "VeRyUn1qU3Me5sAgEiD",
        "source": "https://gbenson.net/hive/libs/messaging/test",
        "type": "net.gbenson.hive.test_event",
        "time": "2025-03-20T08:57:44.512454+00:00",
        "data": {"bonjour": "madame"},
    }


def test_tell_user():
    mock = MockPika()
    mock.exchange_declare = MockMethod()
    mock.basic_publish = MockMethod()

    channel = Channel(pika=mock)
    channel.tell_user("hello world")

    assert mock.exchange_declare.call_log == [((), {
        "exchange": "hive.matrix.requests",
        "exchange_type": "fanout",
        "durable": True,
    })]

    assert len(mock.basic_publish.call_log) == 1
    body = mock.basic_publish.call_log[0][1]["body"]
    assert isinstance(body, bytes)
    assert mock.basic_publish.call_log == [((), {
        "exchange": "hive.matrix.requests",
        "routing_key": "",
        "body": body,
        "properties": BasicProperties(
            content_type="application/cloudevents+json",
            delivery_mode=DeliveryMode.Persistent,
        ),
        "mandatory": True,
    })]

    event = json.loads(body)
    _ = parse_uuid(event.pop("id"))
    event_time = parse_datetime(event.pop("time"))
    delta = (datetime.now().astimezone() - event_time).total_seconds()
    assert 0 < delta < 0.1

    assert event == {
        "specversion": "1.0",
        "source": "https://gbenson.net/hive/services/pytest",
        "type": "net.gbenson.hive.matrix_send_text_request",
        "data": {
            "sender": "hive",
            "text": "hello world",
        },
    }
