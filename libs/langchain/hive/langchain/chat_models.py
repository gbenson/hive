from functools import wraps
from typing import Any, Optional

from langchain.chat_models import init_chat_model as _init_chat_model
from langchain_core.language_models import BaseChatModel

from .ollama import is_ollama_model, configure_ollama_model


@wraps(_init_chat_model)
def init_chat_model(
        model: str,
        *,
        model_provider: Optional[str] = None,
        **kwargs: Any
) -> BaseChatModel:
    if is_ollama_model(model, model_provider):
        kwargs = configure_ollama_model(**kwargs)
    result = _init_chat_model(model, model_provider=model_provider, **kwargs)
    if not isinstance(result, BaseChatModel):
        raise TypeError(type(result).__name__)
    return result
