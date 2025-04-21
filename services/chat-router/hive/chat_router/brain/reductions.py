from . import lstrip, rewrite, rstrip

lstrip("please")
lstrip("i mean")
lstrip("i meant")

for word in ("can", "could", "will", "would", "for"):
    lstrip(f"{word} you")

for word in ("create", "make"):
    rewrite(f"{word} _", "generate *")

for word1 in (
        "choose",
        "draw",
        "generate",
        "imagine",
        "pick",
        "select",
):
    for word2 in ("me", "a", "one", "an"):
        rewrite(f"{word1} {word2} _", f"{word1} *")

rstrip("for me")
rstrip("please")
rstrip("?")
rstrip("!")
rstrip(",")
rstrip(".")

for prefix in (
        "what",
        "whats",
        "what is",
        "what are",
        "tell me",
        "show me",
        "show",
        "print",
):
    for suffix in ("my", "you", "your"):
        rewrite(f"{prefix} {suffix} _", "show *")
