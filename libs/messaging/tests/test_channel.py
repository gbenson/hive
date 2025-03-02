import pytest

from pika import BasicProperties, DeliveryMode

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
        self.call_log.append((args, kwargs))
        return self._returns


class MockCallback(MockMethod):
    def __call__(self, channel: Channel, message: Message):
        return super().__call__(channel, message)


expect_properties = BasicProperties(
    content_type="application/json",
    delivery_mode=DeliveryMode.Persistent,
)


@pytest.mark.filterwarnings("ignore:Call to deprecated method publish_request")
def test_publish_request():
    mock = MockPika()
    mock.exchange_declare = MockMethod()
    mock.basic_publish = MockMethod()

    channel = Channel(pika=mock)
    channel.publish_request(
        message={
            "hello": "world",
        },
        routing_key="hallo.wereld",
    )

    assert mock.exchange_declare.call_log == [((), {
        "exchange": "hive.requests",
        "exchange_type": "direct",
        "durable": True,
    })]
    assert mock.basic_publish.call_log == [((), {
        "exchange": "hive.requests",
        "routing_key": "hallo.wereld",
        "body": b'{"hello": "world"}',
        "properties": expect_properties,
        "mandatory": True,
    })]


@pytest.mark.filterwarnings(
    "ignore:Call to deprecated method consume_requests")
def test_consume_requests():
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
    channel.consume_requests(
        queue="arr.pirates",
        on_message_callback=on_message_callback,
    )

    assert mock.exchange_declare.call_log == [((), {
        "exchange": "hive.requests",
        "exchange_type": "direct",
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
        "exchange": "hive.requests",
        "routing_key": "arr.pirates",
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


def test_publish():
    mock = MockPika()
    mock.exchange_declare = MockMethod()
    mock.basic_publish = MockMethod()

    channel = Channel(pika=mock)
    channel.publish(
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


def test_consume(monkeypatch):
    monkeypatch.delenv("HIVE_EXCLUSIVE_QUEUE_PREFIX", raising=False)

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
    channel.consume(
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
