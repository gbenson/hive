from dataclasses import dataclass
from . import add_canned_response, add_route, router, send_text

CHALLENGE_RESPONSES = (
    ("ping", "pong"),
    ("bonjour", "salop"),
    ("hello", "hi"),
)


@dataclass
class respond_to_challenge:
    lower_challenge: str
    lower_response: str

    def __call__(self) -> None:
        send_text(self.response)()

    @property
    def response(self) -> str:
        lower_response = self.lower_response
        lower_challenge = self.lower_challenge

        for token in router.request.tokens:
            if token.text != lower_challenge:
                continue  # pragma: no cover
            cased_challenge = token.source_text
            if cased_challenge.lower() == lower_challenge:
                break
        else:
            return lower_response  # pragma: no cover

        extra_cased = f"{lower_challenge[0]}{cased_challenge[1:]}"
        cased_challenge = list(cased_challenge)
        while len(cased_challenge) < len(lower_response):
            cased_challenge.extend(extra_cased)
        while len(cased_challenge) > len(lower_response):
            cased_challenge.pop(2)
        assert len(lower_response) == len(cased_challenge)

        user_input = router.request.text

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


for a, b in CHALLENGE_RESPONSES:
    for c, r in ((a, b), (b, a)):
        add_route(f"{c} ^", respond_to_challenge(c, r))
        add_canned_response(f"say {c}", f'you say "{c}", I say "{r}"!')
