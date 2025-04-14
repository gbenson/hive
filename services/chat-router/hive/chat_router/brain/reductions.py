from . import lstrip, rewrite, rstrip

lstrip("please")

for word in ("can", "could", "will", "would"):
    lstrip(f"{word} you")

for word in ("create", "make"):
    rewrite(f"{word} *", "generate *")

for word in ("me", "a", "one"):
    rewrite(f"generate {word} *", "generate *")

rstrip("for me")
rstrip("please")
rstrip("?")
