from functools import cached_property
from typing import Literal, Optional

from pydantic import BaseModel

from hive.common import read_config


class User(BaseModel):
    matrix_id: str
    """Fully-qualified Matrix ID."""

    role: Literal["hive", "user"]
    """Role in Hive."""


class Config(BaseModel):
    users: dict[str, User]

    @classmethod
    def read(cls, config_key: str = "chatbot"):
        return cls.model_validate(read_config(config_key)[config_key])

    @cached_property
    def users_by_matrix_id(self) -> dict[str, User]:
        return {u.matrix_id: u for u in self.users.values()}

    def lookup_user(self, **kwargs: str) -> Optional[User]:
        if len(kwargs) != 1:
            raise TypeError(kwargs)
        key, value = next(iter(kwargs.items()))
        return getattr(self, f"users_by_{key}").get(value)
