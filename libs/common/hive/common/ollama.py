from typing import Any, Optional

from httpx import Timeout
from ollama import Client as _Client

from .endpoint_config import read_endpoint_config
from .httpx import DEFAULT_CLIENT
from .units import MINUTE


# Ollama disables httpx's default timeout of 5 seconds.
# We reenable it, except with a longer read timeout to
# allow for slowness.
_DEFAULT_TIMEOUT_KWARGS = DEFAULT_CLIENT.timeout.as_dict()
_DEFAULT_TIMEOUT_KWARGS["read"] = max(
    _DEFAULT_TIMEOUT_KWARGS.get("read") or 0,
    (5 * MINUTE).total_seconds(),
)
DEFAULT_TIMEOUT = Timeout(**_DEFAULT_TIMEOUT_KWARGS)


class Client(_Client):
    def __init__(self, host: Optional[str] = None, **kwargs: Any):
        kwargs = configure_client(host=host, **kwargs)
        super().__init__(**kwargs)


def configure_client(
        *,
        config_key: Optional[str] = "ollama",
        host: Optional[str] = None,
        timeout: Optional[Timeout] = DEFAULT_TIMEOUT,
        **kwargs: Any
) -> dict[str, Any]:
    if timeout:
        kwargs["timeout"] = timeout

    if not config_key:
        return kwargs

    config = read_endpoint_config(config_key)

    if not host:
        host = config.url if config.url else "http://ollama:11434"

    if host:
        kwargs["host"] = host

        if (config.http_auth and host == config.url and "auth" not in kwargs):
            kwargs["auth"] = config.http_auth.username_password

    return kwargs
