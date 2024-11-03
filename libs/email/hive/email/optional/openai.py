try:
    from hive.common.openai import (
        APIStatusError,
        OpenAI,
    )

except ModuleNotFoundError:
    class APIStatusError(Exception):
        pass

    class OpenAI:
        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError("hive-email[openai] not installed")
