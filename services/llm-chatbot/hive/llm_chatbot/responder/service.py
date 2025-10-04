import logging
import time

from dataclasses import dataclass
from datetime import timedelta
from functools import partial
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable

from hive.common import dynamic_cast, utc_now
from hive.common.langchain import init_chat_model
from hive.common.units import MILLISECOND, SECOND

from langchain_core.language_models import LanguageModelInput

from ..database import ContextID
from ..service import BaseService
from .response_manager import ResponseManager
from .runnables import record_interaction, tokens_to_sentences
from .schema import Message, Request

logger = logging.getLogger(__name__)
d = logger.info


@dataclass
class Service(BaseService):
    """The responder service generates responses to user input.
    """
    max_request_age: timedelta = 30 * SECOND
    tick: timedelta = 500 * MILLISECOND
    tock: timedelta = 30 * SECOND
    default_model: str = "ollama:smollm2:360m"

    @property
    def _tick_ms(self) -> int:
        return round(self.tick / MILLISECOND)

    @property
    def _tock_ms(self) -> int:
        return round(self.tock / MILLISECOND)

    def run(self) -> None:
        self._run(
            stream=self.streams.requests,
            group=self.consumer_group,
            consumer=self.consumer,
        )

    def _run(self, *, stream: str, group: str, consumer: str) -> None:
        self.db.xgroup_create(stream, group, id=0, mkstream=True)

        while True:
            request = self.get_next_request(
                stream=stream,
                group=group,
                consumer=consumer,
            )

            self.on_request(request)

    def get_next_request(
            self,
            *,
            stream: str,
            group: str,
            consumer: str,
    ) -> Request:
        get_next_requests = partial(
            self._get_next_requests,
            stream=stream,
            group=group,
            consumer=consumer,
        )

        # Keep trying to read everything until we get something.
        while not (requests := get_next_requests(block=self._tock_ms)):
            pass

        # Wait until we see a half-second window with no new requests.
        while True:
            # Skip all but the most recent request.
            if (stale_requests := requests[:-1]):
                d("Ignoring %d stale request(s)", len(stale_requests))
                for entry_id, _ in stale_requests:
                    self.db.xack(stream, group, entry_id)
                requests[:-1] = []

            # Now try to read more, for up o half a second.
            assert len(requests) == 1
            requests.extend(get_next_requests(block=self._tick_ms))
            if len(requests) == 1:
                break

        # Ack the request, then validate and return it.
        assert len(requests) == 1
        request_id, values = requests[0]
        self.db.xack(stream, group, request_id)

        d("Decoding %s: %s", request_id, values)

        if (supplied_id := values.get("id")):
            logger.warning("%s: replacing id=%r", request_id, supplied_id)

        return Request.model_validate({**values, "id": request_id})

    def _get_next_requests(
            self,
            *,
            stream: str,
            group: str,
            consumer: str,
            **kwargs: Any
    ) -> list[Any]:
        response = dynamic_cast(
            list,
            self.db.xreadgroup(group, consumer, {stream: ">"}, **kwargs),
        )
        if not response:
            return []
        if len(response) != 1:
            raise ValueError(response)

        stream_requests = dynamic_cast(list, response[0])
        if len(stream_requests) != 2:
            raise ValueError(stream_requests)
        check, requests = stream_requests
        if check != stream:
            raise ValueError(f"Expected: {stream!r}, Got: {check!r}")
        return dynamic_cast(list, requests)

    def on_request(self, request: Request) -> None:
        d("Handling %s", request)
        if not (handle_request := getattr(self, f"on_{request.type}", None)):
            raise NotImplementedError(request.type)
        handle_request(request)

    def on_generate_response(self, request: Request) -> None:
        deadline = request.time + self.max_request_age
        d("Waiting for message: %s", request.message_id)
        while utc_now() < deadline:
            # Get the most recent message in the context?
            message = self.get_latest_message(request.context_id)
            d("Got: %s", message)

            # If the message matches the request then we're golden.
            if message.id == request.message_id:
                self._generate_response(request.context_id, message)
                return

            # If the message is newer then the request got stale.
            if message.time > request.time:
                d("Message %s too new!", message.id)
                return

            # If the message is older then wait a little and try again.
            window = deadline - utc_now()
            self._sleep(self.tick if window > self.tick else window * 0.95)

        d("%s: timed out Waiting for message: %s", request, request.message_id)

    def get_latest_message(self, context_id: ContextID) -> Message:
        ctx_messages = f"ctx:{context_id}:msgs"
        response = dynamic_cast(list, self.db.zrevrangebyscore(
            name=ctx_messages,
            max="+inf",
            min="-inf",
            start=0,
            num=1,
        ))
        if len(response) != 1:
            raise ValueError(response)
        msg_key = f"msg:{response[0]}"
        values = dynamic_cast(dict, self.db.hgetall(msg_key))
        return Message.model_validate(values)

    @staticmethod
    def _sleep(duration: timedelta) -> None:
        seconds = duration.total_seconds()
        if seconds <= 0:
            return
        d("Sleeping for %s seconds", seconds)
        time.sleep(seconds)

    def _generate_response(
            self,
            context_id: ContextID,
            message: Message,
    ) -> None:
        if message.role != "user":
            raise ValueError(message.role)

        d("Generating response for: %s", message)
        with ResponseManager() as rm:
            model_key = f"ctx:{context_id}:model"
            model = dynamic_cast(
                str,
                self.db.get(model_key) or self.default_model
            )

            chain: Runnable[LanguageModelInput, str] = (
                init_chat_model(model)
                | record_interaction(rm._channel, model_input=message.text)
                | StrOutputParser()
                | tokens_to_sentences
            )
            for sentence in chain.stream(message.text):
                rm.send_text(sentence.strip())
