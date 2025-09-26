from pathlib import Path
from typing import Any, Optional

import pytest
import yaml

from pytest import MonkeyPatch

from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatResult

from hive.langchain import chat_models
from hive.common.ollama import DEFAULT_TIMEOUT
from hive.common.testing import test_config_dir  # noqa: F401

from hive.langchain import init_chat_model


def test_no_provider() -> None:
    assert _test_init_chat_model("gpt-4.1-nano") == dict(
        model="gpt-4.1-nano",
        model_provider=None,
    )


def test_non_ollama_provider() -> None:
    assert _test_init_chat_model(
        "gpt-4.1-nano",
        model_provider="openai",
    ) == dict(
        model="gpt-4.1-nano",
        model_provider="openai",
    )


def test_ollama_provider() -> None:
    assert _test_init_chat_model(
        "qwen3:0.6b",
        model_provider="ollama",
    ) == dict(
        model="qwen3:0.6b",
        model_provider="ollama",
        base_url="https://gbenson.net/ollama",
        client_kwargs=dict(
            auth=("hello", "world"),
            timeout=DEFAULT_TIMEOUT,
        ),
    )


def test_non_ollama_provider_in_model() -> None:
    assert _test_init_chat_model("openai:gpt-4.1-nano") == dict(
        model="openai:gpt-4.1-nano",
        model_provider=None,
    )


def test_ollama_provider_in_model() -> None:
    assert _test_init_chat_model("ollama:qwen3:0.6b") == dict(
        model="ollama:qwen3:0.6b",
        model_provider=None,
        base_url="https://gbenson.net/ollama",
        client_kwargs=dict(
            auth=("hello", "world"),
            timeout=DEFAULT_TIMEOUT,
        ),
    )


NON_OLLAMA_VARIATIONS = (
    dict(model="gpt-4.1-nano"),
    dict(model="gpt-4.1-nano", model_provider="openai"),
    dict(model="openai:gpt-4.1-nano"),
)

OLLAMA_VARIATIONS = (
    dict(model="qwen3:0.6b", model_provider="ollama"),
    dict(model="ollama:qwen3:0.6b"),
)

VARIATIONS = NON_OLLAMA_VARIATIONS + OLLAMA_VARIATIONS


@pytest.mark.parametrize("kwargs", VARIATIONS)
def test_no_config(kwargs: dict[str, Any], config_path: Path) -> None:
    """Auth isn't added if we don't have the config file.
    """
    config_path.unlink()
    expect_kwargs = {"model_provider": None, **kwargs}
    if kwargs in OLLAMA_VARIATIONS:
        expect_kwargs["base_url"] = "ollama"
        expect_kwargs["client_kwargs"] = {"timeout": DEFAULT_TIMEOUT}
    assert _test_init_chat_model(**kwargs) == expect_kwargs


@pytest.mark.parametrize("kwargs", NON_OLLAMA_VARIATIONS)
def test_no_auth_wrong_provider(kwargs: dict[str, Any]) -> None:
    """Auth isn't added to non-ollama models even with our base_url.
    """
    kwargs = {"base_url": "https://gbenson.net/ollama", **kwargs}
    expect_kwargs = {"model_provider": None, **kwargs}
    assert _test_init_chat_model(**kwargs) == expect_kwargs


@pytest.mark.parametrize("kwargs", VARIATIONS)
def test_no_auth_wrong_base_url(kwargs: dict[str, Any]) -> None:
    """Auth isn't added if the base_url isn't ours.
    """
    kwargs = {"base_url": "https://gbenson.net/pyjama", **kwargs}
    expect_kwargs = {"model_provider": None, **kwargs}
    if "'ollama" in str(kwargs):
        expect_kwargs["client_kwargs"] = {"timeout": DEFAULT_TIMEOUT}
    assert _test_init_chat_model(**kwargs) == expect_kwargs


@pytest.mark.parametrize(
    "auth",
    (None,
     ("SeKr3T", "p@$$w0rD"),
     ))
@pytest.mark.parametrize(
    "with_base_url",
    (None,
     "https://gbenson.net/ollama",
     "https://gbenson.net/nollama",
     ))
@pytest.mark.parametrize("kwargs", VARIATIONS)
def test_no_overwrite_auth(
        with_base_url: Optional[str],
        auth: Any,
        kwargs: dict[str, Any],
) -> None:
    """Provided auth is never replaced.
    """
    kwargs = {"client_kwargs": {"auth": auth}, **kwargs}
    if with_base_url:
        kwargs["base_url"] = with_base_url

    expect_kwargs = {"model_provider": None, **kwargs}
    if "'ollama" in str(kwargs):
        expect_kwargs["client_kwargs"] = \
            {**expect_kwargs["client_kwargs"], "timeout": DEFAULT_TIMEOUT}
        if not with_base_url:
            expect_kwargs["base_url"] = "https://gbenson.net/ollama"

    assert _test_init_chat_model(**kwargs) == expect_kwargs


# Fixtures etc

@pytest.fixture
def config_path(test_config_dir: str | Path) -> Path:  # noqa: F811
    return Path(test_config_dir) / "ollama.yml"


class MockChatModel(BaseChatModel):
    def __init__(self, model: str, **kwargs: Any):
        self._mock_chat_model_kwargs = {"model": model, **kwargs}

    @property
    def _llm_type(self) -> str:
        raise NotImplementedError

    def _generate(
            self,
            *args: Any,
            **kwargs: Any
    ) -> ChatResult:
        raise NotImplementedError


@pytest.fixture(autouse=True)
def common_setup(config_path: Path, monkeypatch: MonkeyPatch) -> None:
    config_path.write_text(yaml.dump({
        "ollama": {
            "url": "https://gbenson.net/ollama",
            "http_auth": {
                "username": "hello",
                "password": "world",
            },
        },
    }))
    monkeypatch.setattr(
        chat_models,
        "_init_chat_model",
        MockChatModel,
    )


def _test_init_chat_model(*args: Any, **kwargs: Any) -> dict[str, Any]:
    model = init_chat_model(*args, **kwargs)
    assert isinstance(model, MockChatModel)
    return model._mock_chat_model_kwargs
