import json

from dataclasses import dataclass

from pika.spec import Basic, BasicProperties


@dataclass
class Message:
    method: Basic.Deliver
    properties: BasicProperties
    body: bytes

    @property
    def content_type(self) -> str:
        return self.properties.content_type

    def json(self):
        if self.content_type != "application/json":
            raise ValueError(self.content_type)
        return json.loads(self.body)
