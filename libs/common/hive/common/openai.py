from . import read_config

try:
    from openai import (
        APIStatusError,
        OpenAI as _OpenAI,
    )

except ModuleNotFoundError:
    class APIStatusError(Exception):
        pass

    class _OpenAI:
        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError("hive-common[openai] not installed")


class OpenAI(_OpenAI):
    def __init__(self, **kwargs):
        api_key = kwargs.pop("api_key", None)
        if not api_key:
            api_key = read_config("openai")["api_key"]
        super().__init__(api_key=api_key, **kwargs)
