from functools import wraps
from typing import Any, Optional

from langchain.chat_models import init_chat_model as _init_chat_model
from pydantic import BaseModel

from .config import read as read_config


@wraps(_init_chat_model)
def init_chat_model(
        model: str,
        *,
        model_provider: Optional[str] = None,
        **kwargs: Any
) -> Any:
    if _is_ollama_model(model, model_provider):
        if (config := _read_config("ollama")):
            kwargs = _configure_ollama_model(config, **kwargs)
    return _init_chat_model(model, model_provider=model_provider, **kwargs)


def _is_ollama_model(model: str, model_provider: Optional[str]) -> bool:
    return (model_provider == "ollama"
            if model_provider
            else model.startswith("ollama:"))


class Auth(BaseModel):
    username: str
    password: str

    def _as_tuple(self) -> tuple[str, str]:
        return self.username, self.password


class EndpointConfig(BaseModel):
    url: Optional[str] = None
    http_auth: Optional[Auth] = None


def _read_config(config_key: str) -> Optional[EndpointConfig]:
    try:
        config_dict = read_config(config_key)[config_key]
    except KeyError:
        return None
    return EndpointConfig.model_validate(config_dict)


def _configure_ollama_model(
        config: EndpointConfig,
        *,
        base_url: Optional[str] = None,
        client_kwargs: Optional[dict[str, Any]] = None,
        **kwargs: Any
) -> dict[str, Any]:
    if not base_url:
        if config.url:
            base_url = config.url

    if base_url:
        kwargs["base_url"] = base_url

        if (config.http_auth
            and base_url == config.url
            and (not client_kwargs
                 or "auth" not in client_kwargs)):

            if not client_kwargs:
                client_kwargs = {}
            client_kwargs["auth"] = config.http_auth._as_tuple()

    if client_kwargs:
        kwargs["client_kwargs"] = client_kwargs

    return kwargs
