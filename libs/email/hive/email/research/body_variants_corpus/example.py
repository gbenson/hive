import json
import logging

from dataclasses import dataclass
from typing import Optional

from hive.common import read_resource

from ...optional.openai import APIStatusError, OpenAI

logger = logging.getLogger(__name__)
d = logger.debug
info = logger.info
warn = logger.warning


@dataclass
class Example:
    _id: str
    plaintext_variant: str
    generated_variant: str
    best_variant: Optional[str] = None
    explanation: Optional[str] = None

    def as_dict(self):
        result = {
            "id": self._id,
            "variants": {
                "plaintext": self.plaintext_variant,
                "generated": self.generated_variant,
            },
            "best_variant": self.best_variant,
        }
        if self.explanation:
            result["explanation"] = self.explanation
        return result

    @classmethod
    def from_json(cls, serialized: str):
        kwargs = json.loads(serialized)
        _id = kwargs.pop("id")
        variants = kwargs.pop("variants")
        best_variant = kwargs.pop("best_variant")
        kwargs.update(
            (f"{k}_variant", v)
            for k, v in variants.items()
        )
        if best_variant is None:
            best_variant = "not-decidable"
        return cls(_id, best_variant=best_variant, **kwargs)

    CHOOSER_PROMPT = read_resource("prompts/choose_best_variant.md")

    _RESULT_MAP = {
        "plain": "plaintext",
        "markdown": "generated",
    }

    def categorize(self, openai: OpenAI):
        assert not (self.best_variant or self.explanation)
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "system",
                    "content": self.CHOOSER_PROMPT,
                }, {
                    "role": "user",
                    "content": json.dumps({
                        "plain_text": self.plaintext_variant,
                        "markdown": self.generated_variant,
                    }),
                }],
                temperature=0,
            )
        except APIStatusError as e:
            self.explanation = e.response.json()["error"]["message"]
            self.best_variant = "not-decidable"
            return

        d(response.json())

        if len(response.choices) != 1:
            raise NotImplementedError(response.json())
        try:
            llm_output_json = response.choices[0].message.content
        except Exception as e:
            raise NotImplementedError(response.json()) from e
        try:
            llm_output = json.loads(llm_output_json)
            llm_result = llm_output["best_version"]
        except Exception as e:
            raise NotImplementedError(llm_output_json) from e

        if (result := self._RESULT_MAP.get(llm_result)):
            self.best_variant = result
            return

        self.explanation = llm_output.get("explanation")
        warn("%s: %s: %s", self._id, llm_result, self.explanation)
        if llm_result != "not-decidable":
            raise NotImplementedError(llm_output_json)

        self.best_variant = llm_result
