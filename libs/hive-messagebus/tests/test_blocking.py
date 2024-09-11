from datetime import datetime

from hive import messagebus as msgbus


def test_send_to_queue(test_credentials):
    sent_msg = {"timestamp": str(datetime.now())}
    test_queue = "test.message_bus.send_recv"
    msgbus.send_to_queue(test_queue, sent_msg)
