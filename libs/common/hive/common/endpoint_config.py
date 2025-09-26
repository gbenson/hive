from typing import Optional, TypeVar

from pydantic import BaseModel

from .config import read as _read_config

T = TypeVar("T", bound="EndpointConfig")


class Auth(BaseModel):
    username: str
    password: str

    @property
    def username_password(self) -> tuple[str, str]:
        return self.username, self.password


class EndpointConfig(BaseModel):
    url: Optional[str] = None
    http_auth: Optional[Auth] = None

    @classmethod
    def read(cls: type[T], config_key: str) -> T:
        try:
            config_dict = _read_config(config_key)[config_key]
        except KeyError:
            config_dict = {}
        return cls.model_validate(config_dict)


read_endpoint_config = EndpointConfig.read
