from typing import Any

import pytest

from hive.common.dictutil import flatten, update_noreplace


@pytest.mark.parametrize(
    "input,expect_output",
    (({}, {}),
     ({
         "context_id": "63960e88-32d5-4bf6-b951-2b045529e487",
         "message": {
                 "id": "50937a35-3b37-4007-8aa8-99f67415f42b",
                 "role": "user",
                 "content": {"type": "text", "text": "Hello"},
         },
     }, {
         "context_id": "63960e88-32d5-4bf6-b951-2b045529e487",
         "message.id": "50937a35-3b37-4007-8aa8-99f67415f42b",
         "message.role": "user",
         "message.content.type": "text",
         "message.content.text": "Hello",
     }),
     ))
def test_flatten(input: dict[str, Any], expect_output: dict[str, Any]) -> None:
    assert flatten(input) == expect_output


def test_flatten_fail() -> None:
    with pytest.raises(TypeError) as ex:
        _ = flatten({"hello": {"what": "world", "more": [1, 2, 3]}})
    assert str(ex.value) == "list"


def test_update_noreplace() -> None:
    d = {"hello": "world"}
    update_noreplace(d, what_time="is it?")
    assert d == {"hello": "world", "what_time": "is it?"}


def test_update_noreplace_fail() -> None:
    d = {"hello": "world"}
    with pytest.raises(ValueError) as ex:
        update_noreplace(d, what_time="is it?", hello="japan")
    assert str(ex.value) == "hello"
