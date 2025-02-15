from hive.common.llm import LLMToolbox, llm_tool


class TestToolbox(LLMToolbox):
    @llm_tool
    def get_current_weather(self, city: str):
        """Get the current weather for a city.

        :param city: The name of the city.
        """

    def test_llm_tool_decorated(self):
        assert self.get_current_weather.__llm_tool__

    def test_llm_tools_property(self):
        assert self.llm_tools == [
            {
                "type": "function",
                "function": {
                    "name": "get_current_weather",
                    "description": "Get the current weather for a city.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "The name of the city.",
                            },
                        },
                        "required": ["city"],
                    },
                },
            },
        ]
