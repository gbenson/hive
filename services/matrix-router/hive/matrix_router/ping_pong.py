from typing import Optional

from hive.messaging import Channel


_RESPONSES = {
    "ping": "pong",
    "bonjour": "salop",
    "hello": "world",
}


def response_for_challenge(challenge: str) -> Optional[str]:
    chal = challenge.strip()
    x = sum(c == "!" or c.isupper() for c in chal[1:])
    chal = chal.strip("!")
    resp = _RESPONSES.get(chal.lower())
    if not resp:
        return None
    chal = list(chal)
    while len(chal) > len(resp):
        chal.pop(2)
    assert len(resp) == len(chal)
    result = [b.upper() if a.isupper() else b for a, b in zip(chal, resp)]
    return "".join(result) + ("!" * x)


def route_response_for_challenge(channel: Channel, response: str):
    channel.publish_request(
        message={
            "format": "text",
            "messages": [response]
        },
        routing_key="matrix.message.send.requests",
    )
