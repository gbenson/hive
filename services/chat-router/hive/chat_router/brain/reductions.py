from . import lstrip, rewrite, rstrip

lstrip("please")

for word in ("can", "could", "will", "would"):
    lstrip(f"{word} you")

for word in ("create", "make"):
    rewrite(f"{word} *", "generate *")

for word in ("me", "a", "one", "an"):
    rewrite(f"draw {word} *", "draw *")
    rewrite(f"generate {word} *", "generate *")

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
        rewrite(f"{prefix} {suffix} *", "show *")
