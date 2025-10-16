# from ..tokenizer import Token
from . import rewrite  # ,route

for word in ("choose", "pick", "select"):
    rewrite(f"{word} _", "random *")

for word in ("name", "word", "noun", "verb", "adjective", "adverb"):
    rewrite(f"_ {word} ?", f"random * {word}")
    rewrite(f"_ {word}s ?", f"random * {word}s")

rewrite("generate random *", "random *")
rewrite("generate * random *", "random * *")


# @route(patterns=(
#     "random * name",
#     "random * names",
# ))
# def random_name(*args: Token) -> None:
#     raise NotImplementedError("name")


# @route(pattern="random *")
# def random_word(*args: Token) -> None:
#     raise NotImplementedError("word")
