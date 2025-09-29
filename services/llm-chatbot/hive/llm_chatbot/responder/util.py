import re

from collections import defaultdict
from collections.abc import Iterator

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import BaseMessageChunk
from langchain_core.runnables import RunnableGenerator

from pydantic import BaseModel

from hive.messaging import Channel


def tokens_to_sentences(input: Iterator[str]) -> Iterator[str]:
    SEP = re.compile(r"((?:(?<=\D)\.(?=\D))|\n)", re.DOTALL)
    buf = ""
    for token in input:
        buf += token
        splits = SEP.split(buf, maxsplit=1)
        if len(splits) == 1:
            continue
        assert len(splits) == 3
        buf = splits.pop()
        if (sentence := "".join(splits[:2]).strip()):
            yield sentence
    if (sentence := buf.strip()):
        yield sentence


class InteractionRecord(BaseModel):
    model_input: LanguageModelInput
    model_output: list[BaseMessageChunk]


def record_interaction(
        channel: Channel,
        *,
        routing_key: str = "llm.interactions",
        model_input: LanguageModelInput,
) -> RunnableGenerator[BaseMessageChunk, BaseMessageChunk]:
    def transform(
            input: Iterator[BaseMessageChunk],
    ) -> Iterator[BaseMessageChunk]:
        chunks = defaultdict(list)
        for chunk in input:
            yield chunk

            run_id = getattr(chunk, "id", None)
            chunks[run_id].append(chunk)

            md = getattr(chunk, "response_metadata", None)
            if not (md and md.get("done")):
                continue

            channel.maybe_publish_event(
                data=InteractionRecord(
                    model_input=model_input,
                    model_output=chunks.pop(run_id),
                ),
                routing_key=routing_key,
            )
    return RunnableGenerator(transform)
