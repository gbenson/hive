import os

from hive.common.openai import _OpenAI, OpenAI
from hive.common.testing import test_config_dir  # noqa: F401


def test_openai(test_config_dir, monkeypatch):  # noqa: F811
    with open(os.path.join(test_config_dir, "openai.env"), "w") as fp:
        print("OPENAI_API_KEY=BLrnKp+hf5Qyn7UqH2RFHGX/smwlqDW", file=fp)

    calls = []
    def log_call(*args, **kwargs):
        calls.append((args, kwargs))

    with monkeypatch.context() as mp:
        mp.setattr(_OpenAI, "__init__", log_call)
        client = OpenAI()

    assert calls == [
        ((client,), {"api_key": "BLrnKp+hf5Qyn7UqH2RFHGX/smwlqDW"}),
    ]
