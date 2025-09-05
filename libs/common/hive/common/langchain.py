from functools import wraps
from typing import Any, Optional

from langchain.chat_models import init_chat_model as _init_chat_model

from .endpoint_config import EndpointConfig, read_endpoint_config


@wraps(_init_chat_model)
def init_chat_model(
        model: str,
        *,
        model_provider: Optional[str] = None,
        **kwargs: Any
) -> Any:
    if _is_ollama_model(model, model_provider):
        if (config := read_endpoint_config("ollama")):
            kwargs = _configure_ollama_model(config, **kwargs)
    return _init_chat_model(model, model_provider=model_provider, **kwargs)


def _is_ollama_model(model: str, model_provider: Optional[str]) -> bool:
    return (model_provider == "ollama"
            if model_provider
            else model.startswith("ollama:"))


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
            client_kwargs["auth"] = config.http_auth.username_password

    if client_kwargs:
        kwargs["client_kwargs"] = client_kwargs

    return kwargs
