from dataclasses import astuple, dataclass

from hive.chat_router.tokenizer import Token, SpecialToken


@dataclass
class T:
    text: str
    start: int
    limit: int
    starts_word: bool = True

    def as_token(self, source: str) -> Token:
        token = Token.from_string(source, *astuple(self)[1:])
        return token.with_text(self.text)


class S(T):
    def as_token(self, source: str) -> Token:
        assert len(self.text) == 1
        return SpecialToken.maybe_capture_one(
            self.text,
            super().as_token(source),
        )
