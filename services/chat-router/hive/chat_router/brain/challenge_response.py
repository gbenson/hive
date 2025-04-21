from dataclasses import dataclass
from . import add_canned_response, add_route, rewrite, router, send_text

CHALLENGE_RESPONSES = (
    ("ping", "pong"),
    ("bonjour", "salop"),
    ("hello", "hi"),
    ("yo", "hey"),
    ("thanks", "welcome"),
    ("thx", "yw"),
)

for challenge in ("thank you", "ta", "tvm"):
    rewrite(challenge, "thanks")

rewrite("gg", "thx")

for pre_challenge in ("you're", "your", "you"):
    rewrite(f"{pre_challenge} welcome", "welcome")


@dataclass
class respond_to_challenge:
    lower_challenge: str
    lower_response: str

    def __call__(self) -> None:
        send_text(self.response)()

    @property
    def response(self) -> str:
        lower_challenge = self.lower_challenge

        lower_response = self.lower_response
        if lower_response == "welcome":
            lower_response = "you're welcome!"

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
        # XXX this should work with just a route for f"{c} #",
        # except non-matching sharp matches at the end of the
        # pattern doesn't bump the priority like it should :(
        respond = respond_to_challenge(c, r)
        for challenge in (c, f"{c} #"):
            add_route(challenge, respond_to_challenge(c, r))
        add_canned_response(f"say {c}", f'you say "{c}", I say "{r}"!')


for when in ("morning", "afternoon", "evening"):
    rewrite(f"good {when} ^", "hi")

rewrite("hive ?", "hi!")
rewrite("salut", "salop")
