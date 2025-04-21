from hive.chat_router.brain import router
from hive.chat_router.tokenizer import tokenize


def test_matcher():
    s = "please could you generate me 14 random male names please?"
    matcher = router.graph.match(tuple(tokenize(s)))
    print(matcher)
    assert matcher
    matches = matcher.matches
    assert len(matches) == 3

    assert [m.pattern for m in matches] == [
        "_ ?",
        "please _",
        "*",
    ]
    assert [" ".join(s.match for s in m.groups) for m in matches] == [
        "please could you generate me 14 random male names please",
        "could you generate me 14 random male names please ?",
        "please could you generate me 14 random male names please ?",
    ]
    assert matcher.best_match is matches[1]
