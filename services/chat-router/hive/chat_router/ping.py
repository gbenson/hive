import logging
import re

from typing import Optional

from hive.chat import tell_user
from hive.messaging import Channel

logger = logging.getLogger(__name__)
d = logger.info


def handle_ping(channel: Channel, challenge: str) -> bool:
    response = response_for_challenge(challenge)
    if not response:
        return False
    d("Challenge: %r: Response: %r", challenge, response)
    tell_user(response, channel=channel)
    return True


STATIC_RESPONSES = {
    "ping": "pong",
    "pong": "ping",
    "bonjour": "salop",
    "salop": "bonjour",
    "hello": "hi",
    "hi": "hello",
}


def response_for_challenge(challenge: str) -> Optional[str]:
    user_input = challenge.strip()
    cased_challenge = the_one_word(user_input)
    if not cased_challenge:
        return None

    lower_challenge = cased_challenge.lower()
    lower_response = STATIC_RESPONSES.get(lower_challenge)
    if not lower_response:
        return None

    extra_cased = f"{lower_challenge[0]}{cased_challenge[1:]}"
    cased_challenge = list(cased_challenge)
    while len(cased_challenge) < len(lower_response):
        cased_challenge.extend(extra_cased)
    while len(cased_challenge) > len(lower_response):
        cased_challenge.pop(2)
    assert len(lower_response) == len(cased_challenge)

    response = [
        b.upper() if a.isupper() else b
        for a, b in zip(cased_challenge, lower_response)
    ]

    if (x := sum(1 for c in user_input if c == "!")):
        response.append("!" * x)  # match num excls in user input
    elif len(user_input) > len(lower_challenge):
        response.append("!")  # there was punctuation
    elif not lower_challenge[1:] in user_input:
        response.append("!")  # uppercase after first letter

    return "".join(response)


def the_one_word(s: str) -> Optional[str]:
    words = re.finditer(r"\w+", s)
    try:
        first_match = next(words)
    except StopIteration:
        return None
    try:
        _ = next(words)
        return None
    except StopIteration:
        return first_match.group(0)
