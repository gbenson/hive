from functools import wraps
from typing import Any, Optional

from langchain.chat_models import init_chat_model as _init_chat_model
from langchain_core.language_models import BaseChatModel

from .ollama import configure_client as configure_ollama_client


@wraps(_init_chat_model)
def init_chat_model(
        model: str,
        *,
        model_provider: Optional[str] = None,
        **kwargs: Any
) -> BaseChatModel:
    if _is_ollama_model(model, model_provider):
        kwargs = configure_ollama_model(**kwargs)
    if model_provider:
        kwargs = {"model_provider": model_provider, **kwargs}
    result = _init_chat_model(model, **kwargs)
    if not isinstance(result, BaseChatModel):
        raise TypeError(type(result).__name__)
    return result


def _is_ollama_model(model: str, model_provider: Optional[str]) -> bool:
    return (model_provider == "ollama"
            if model_provider
            else model.startswith("ollama:"))


def configure_ollama_model(
        *,
        client_kwargs: Optional[dict[str, Any]] = None,
        **kwargs: Any
) -> dict[str, Any]:
    if not client_kwargs:
        client_kwargs = dict()

    if "base_url" in kwargs:
        if "host" in client_kwargs:
            raise ValueError
        client_kwargs["host"] = kwargs.pop("base_url")

    if "timeout" in kwargs:
        if "timeout" in client_kwargs:
            raise ValueError
        client_kwargs["timeout"] = kwargs.pop("timeout")

    client_kwargs = configure_ollama_client(**client_kwargs)

    if (base_url := client_kwargs.pop("host", None)):
        kwargs["base_url"] = base_url

    if client_kwargs:
        kwargs["client_kwargs"] = client_kwargs

    return kwargs
