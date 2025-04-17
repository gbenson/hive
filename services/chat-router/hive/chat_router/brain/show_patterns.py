from . import add_route, rewrite, router, send_text

COMMAND = "patterns"
ALIASES = ("graph", "pattern graph")


def show_patterns():
    send_text(str(router.graph))()


VARIANTS = (COMMAND,) + ALIASES

add_route(COMMAND, show_patterns)

for alias in ALIASES:
    rewrite(alias, COMMAND)

for variant in VARIANTS:
    rewrite(f"show {variant}", COMMAND)
