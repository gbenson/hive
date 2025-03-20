import json
import re

from dataclasses import dataclass

from pika.spec import Basic, BasicProperties

APPLICATION_JSON_RE = re.compile(r"application/(:?.+\+)?json")


@dataclass
class Message:
    method: Basic.Deliver
    properties: BasicProperties
    body: bytes

    @property
    def correlation_id(self) -> str:
        return self.properties.correlation_id

    @property
    def content_type(self) -> str:
        return self.properties.content_type

    def json(self):
        if not APPLICATION_JSON_RE.fullmatch(self.content_type):
            raise ValueError(self.content_type)
        return json.loads(self.body)
