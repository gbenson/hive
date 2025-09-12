import sys

from unittest.mock import Mock

from hive.messaging import Message, blocking_connection


def main():
    events = []
    props = Mock(content_type="application/cloudevents+json")
    for line in sys.stdin.readlines():
        msg = Message(None, props, line.encode("utf-8"))
        events.append(msg.event())
    print("Loaded", len(events), "events")

    with blocking_connection() as conn:
        channel = conn.channel()
        for index, event in enumerate(events):
            print(f"{index + 1}/{len(events)}")
            channel.publish_request(
                message=event,
                routing_key="llm.chatbot.requests",
            )
        print("Done!")
        print("(now press Ctrl-C)")
        channel.start_consuming()
