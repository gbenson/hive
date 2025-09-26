from typing import Any, Optional

try:
    from hive.common.ollama import configure_client
except ModuleNotFoundError:
    def configure_client(**kwargs: Any) -> dict[str, Any]:  # type: ignore
        raise ModuleNotFoundError("hive-langchain[ollama] not installed")


def is_ollama_model(model: str, model_provider: Optional[str]) -> bool:
    return (model_provider == "ollama"
            if model_provider
            else model.startswith("ollama:"))


def configure_ollama_model(
        *,
        base_url: Optional[str] = None,
        client_kwargs: Optional[dict[str, Any]] = None,
        **kwargs: Any
) -> dict[str, Any]:
    if not client_kwargs:
        client_kwargs = dict()

    if "timeout" in kwargs:
        if "timeout" in client_kwargs:
            raise ValueError
        client_kwargs["timeout"] = kwargs.pop("timeout")

    client_kwargs = configure_client(host=base_url, **client_kwargs)

    if (base_url := client_kwargs.pop("host", None)):
        kwargs["base_url"] = base_url

    if client_kwargs:
        kwargs["client_kwargs"] = client_kwargs

    return kwargs
