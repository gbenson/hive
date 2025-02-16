from collections.abc import Iterable
from dataclasses import dataclass
from inspect import get_annotations, stack
from typing import Any, Callable, ClassVar, TypeVar


class LLMToolbox:
    @property
    def llm_tools(self) -> list[dict[str, Any]]:
        locs = [(frame.filename, frame.lineno) for frame in stack()]
        if locs[1] in locs[2:]:
            return []  # recursion!
        return list(self._llm_tools)

    @property
    def _llm_tools(self) -> Iterable[dict[str, Any]]:
        for name in dir(self):
            if name.startswith("_"):
                continue
            candidate = getattr(self, name)
            if not getattr(candidate, "__llm_tool__", False):
                continue
            yield LLMTool(name, candidate).definition


@dataclass
class LLMTool:
    name: str
    func: Callable

    @property
    def definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    @property
    def description(self) -> str:
        return self.func.__doc__.partition(":param ")[0].strip()

    @property
    def parameters(self) -> dict[str, Any]:
        params = dict(self._parameters)
        return {
            "type": "object",
            "properties": params,
            "required": list(params.keys()),
        }

    @property
    def _parameters(self) -> Iterable[str, dict[str, Any]]:
        for param_doc in self.func.__doc__.split(":param ")[1:]:
            name, description = param_doc.split(":", 1)
            _type = get_annotations(self.func)[name]
            yield name, {
                "type": self._TYPE_NAMES[_type],
                "description": description.strip(),
            }

    _TYPE_NAMES: ClassVar[dict[TypeVar, str]] = {
        int: "integer",
        str: "string",
    }
    _TYPE_NAMES.update(
        (key.__name__, value)
        for key, value in list(_TYPE_NAMES.items())
    )


def llm_tool(func):
    """Decorator."""
    func.__llm_tool__ = True
    return func
