import json

from typing import Any

from pydantic import BaseModel, ConfigDict

from hive.messaging import Channel


class Encapsulated(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    payload: bytes
    content_type: str


def encapsulate(**kwargs: Any) -> Encapsulated:
    return Encapsulated(**dict(zip(
        ("payload", "content_type"),
        Channel._encapsulate(**kwargs)
    )))


def test_encapsulate_dict() -> None:
    e = encapsulate(data={"hello": "world"}, routing_key="e.ds")
    assert e.content_type == "application/cloudevents+json"
    assert json.loads(e.payload)["data"] == {"hello": "world"}


def test_encapsulate_pydantic() -> None:
    class Data(BaseModel):
        hello: str

    e = encapsulate(data=Data(hello="world"), routing_key="e.ps")
    assert e.content_type == "application/cloudevents+json"
    assert json.loads(e.payload)["data"] == {"hello": "world"}
