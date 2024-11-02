import re

from typing import Optional

from hive.messaging import Channel


CHALLENGE_RESPONSES = {
    "ping": "pong",
    "bonjour": "salop",
    "hello": "hi",
}

_WORD_RE = re.compile(r"\w+")


def _the_one_word(s: str) -> Optional[str]:
    words = _WORD_RE.finditer(s)
    try:
        first_match = next(words)
    except StopIteration:
        return None
    try:
        _ = next(words)
        return None
    except StopIteration:
        return first_match.group(0)


def response_for_challenge(challenge: str) -> Optional[str]:
    challenge = challenge.strip()
    chal = _the_one_word(challenge)
    if not chal:
        return None
    lcha = chal.lower()
    resp = CHALLENGE_RESPONSES.get(lcha)
    if not resp:
        return None
    chal = list(chal)
    while len(chal) > len(resp):
        chal.pop(2)
    assert len(resp) == len(chal)
    result = [b.upper() if a.isupper() else b for a, b in zip(chal, resp)]
    if (x := sum(1 for c in challenge if c == "!")):
        result.append("!" * x)  # excls in challenge
    elif len(challenge) != len(lcha):
        result.append("!")  # punctuation
    elif not lcha[1:] in challenge:
        result.append("!")  # uppercase
    return "".join(result)


def route_response_for_challenge(channel: Channel, response: str):
    channel.publish_request(
        message={
            "format": "text",
            "messages": [response]
        },
        routing_key="matrix.message.send.requests",
    )
