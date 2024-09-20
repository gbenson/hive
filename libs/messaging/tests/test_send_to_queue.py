import logging

from datetime import datetime

from hive import messaging as msgbus
from hive.common.testing import want_to_see


def test_send_to_queue(test_credentials, caplog):
    sent_msg = {"timestamp": str(datetime.now())}
    test_queue = "test.message_bus.send_recv"
    with caplog.at_level(logging.DEBUG, logger="pika"):
        msgbus.send_to_queue(test_queue, sent_msg)

    # Ensure we saw the broker confirm receipt of our message
    want_to_see(caplog, "Processing 1:Basic.Ack")

    # Ensure we initiated closing the channel
    want_to_see(caplog, "Closing connection (200): Normal shutdown")
