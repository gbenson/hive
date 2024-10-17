import json
import logging

from dataclasses import dataclass
from typing import Optional

from hive.common import read_resource

from ...optional.openai import APIStatusError, OpenAI

logger = logging.getLogger(__name__)
d = logger.debug


@dataclass
class Example:
    _id: str
    text_variant: str
    html_variant: str
    category: Optional[str] = None

    def as_dict(self):
        result = {
            "id": self._id,
            "variants": {
                "text": self.text_variant,
                "html": self.html_variant,
            },
        }
        if self.category:
            result["category"] = self.category
        return result

    @classmethod
    def from_json(cls, serialized: str):
        kwargs = json.loads(serialized)
        _id = kwargs.pop("id")
        variants = kwargs.pop("variants")
        kwargs.update(
            (f"{k}_variant", v)
            for k, v in variants.items()
        )
        return cls(_id, **kwargs)

    PROMPT = read_resource("prompts/identify_placeholders.md")

    def categorize(self, openai: OpenAI):
        assert not self.category
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.PROMPT},
                    {"role": "user", "content": self.text_variant},
                ],
                temperature=0,
            )
        except APIStatusError as e:
            raise NotImplementedError(
                e.response.json()["error"]["message"],
            ) from e

        d(response.json())

        if len(response.choices) != 1:
            raise NotImplementedError(response.json())
        try:
            llm_output_json = response.choices[0].message.content
        except Exception as e:
            raise NotImplementedError(response.json()) from e
        try:
            llm_output = json.loads(llm_output_json.strip("`"))
            self.category = llm_output["category"]
        except Exception as e:
            raise NotImplementedError(llm_output_json) from e
