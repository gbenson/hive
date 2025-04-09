import pytest

from hive.chat_router.tokenizer import split, expand, EXPANSIONS


@pytest.mark.parametrize(
    "contraction,expansion",
    tuple(sorted(EXPANSIONS.items())),
)
def test_expand(contraction, expansion):
    cs = tuple(split(contraction))
    assert len(cs) == 1
    c = cs[0]
    assert c.text == contraction
    assert c.start == 0
    assert c.limit == len(contraction)

    xs = tuple(expand(c))
    assert len(xs) == 2
    a, b = xs
    assert a.start == c.start
    assert b.start == a.limit
    assert b.limit == c.limit
    assert a.limit > a.start
    assert b.limit > b.start
