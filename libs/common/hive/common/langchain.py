from functools import wraps
from typing import Any, Optional

from langchain.chat_models import init_chat_model as _init_chat_model

from .ollama import configure_client as configure_ollama_client


@wraps(_init_chat_model)
def init_chat_model(
        model: str,
        *,
        model_provider: Optional[str] = None,
        **kwargs: Any
) -> Any:
    if _is_ollama_model(model, model_provider):
        kwargs = configure_ollama_model(**kwargs)
    return _init_chat_model(model, model_provider=model_provider, **kwargs)


def _is_ollama_model(model: str, model_provider: Optional[str]) -> bool:
    return (model_provider == "ollama"
            if model_provider
            else model.startswith("ollama:"))


def configure_ollama_model(
        *,
        base_url: Optional[str] = None,
        client_kwargs: Optional[dict[str, Any]] = None,
        **kwargs: Any
) -> dict[str, Any]:
    kwargs = configure_ollama_client(
        host=base_url,
        auth=client_kwargs.get("auth") if client_kwargs else None,
        **kwargs
    )

    if (base_url := kwargs.pop("host", None)):
        kwargs["base_url"] = base_url

    if (auth := kwargs.pop("auth", None)):
        if not client_kwargs:
            client_kwargs = {}
        client_kwargs["auth"] = auth

    if client_kwargs:
        kwargs["client_kwargs"] = client_kwargs

    return kwargs
