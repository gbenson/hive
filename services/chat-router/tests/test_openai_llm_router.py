from pathlib import Path

import pytest

# from openai.types.chat import ChatCompletionMessageToolCall

from hive.chat import ChatMessage
from hive.chat_router.handlers.openai_llm_router import (
    LLMInteraction,
    LLMToolCall,
)
from hive.common.testing import test_config_dir  # noqa: F401

ChatCompletionMessageToolCall = NotImplemented


@pytest.fixture
def test_interaction(test_config_dir) -> LLMInteraction:  # noqa: F811
    (Path(test_config_dir) / "openai.env").write_text(
        "OPENAI_API_KEY=this-is-not-my-openai-key\n",
    )
    return LLMInteraction(ChatMessage("email for smol?"))


@pytest.fixture
def test_tool_call() -> LLMToolCall:
    return LLMToolCall(
        tool_call_id="call_cnnw1R7su9JdYCh726zs1ZQr",
        function_name="get_email_address_for_service",
        arguments={"service": "smol"},
    )


@pytest.mark.skip
def test_request_message(test_interaction):
    assert test_interaction.api_request["messages"][-1] == {
        "role": "user",
        "content": "email for smol?",
    }


@pytest.mark.skip
def test_request_tools(test_interaction):
    assert sorted([
        tool["function"]["name"]
        for tool in test_interaction.api_request["tools"]
    ]) == [
        "get_email_address_for_service",
        "get_password_for_service",
    ]


@pytest.mark.skip
def test_parse_tool_calls(test_interaction, test_tool_call):
    assert list(test_interaction.parse_tool_calls([
        ChatCompletionMessageToolCall(
            id="call_cnnw1R7su9JdYCh726zs1ZQr",
            type="function",
            function={
                "name": "get_email_address_for_service",
                "arguments": '{"service":"smol"}',
            },
        )])) == [test_tool_call]


def test_tool_call_as_text(test_tool_call):
    assert test_tool_call.as_text() == \
        '[tool call: get_email_address_for_service(service="smol")]'


def test_tool_call_as_html(test_tool_call):
    assert test_tool_call.as_html() == (
        '<span class="unsent">'
        '<span class="unseen">[tool call: </span>'
        "get_email_address_for_service"
        '<span class="unseen">(service=&quot;</span>'
        "smol"
        '<span class="unseen">&quot;)]</span></span>'
    )
