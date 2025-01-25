import logging
import time

from dataclasses import dataclass
from typing import ClassVar, Optional

from transformers import AutoModelForCausalLM, AutoTokenizer

from hive.common import ArgumentParser
from hive.messaging import Channel, Message
from hive.service import HiveService

logger = logging.getLogger(__name__)
d = logger.info


@dataclass
class Service(HiveService):
    DEFAULT_MODEL: ClassVar[str] = "Qwen/Qwen2.5-0.5B-Instruct"
    model_name: Optional[str] = None
    model: Optional[AutoModelForCausalLM] = None
    tokenizer: Optional[AutoTokenizer] = None
    request_queue: str = "local.llm.requests"

    def make_argument_parser(self) -> ArgumentParser:
        parser = super().make_argument_parser()
        parser.add_argument(
            "--model",
            default=self.DEFAULT_MODEL,
            help=f"model to use [default: {self.DEFAULT_MODEL}]",
        )
        return parser

    def __post_init__(self):
        super().__post_init__()
        if self.model_name is None:
            self.model_name = self.args.model
        if self.model is None:
            d("Loading model")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype="auto",
                device_map="auto",
            )
        if self.tokenizer is None:
            d("Loading tokenizer")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name
            )

    def on_request(self, channel: Channel, message: Message):
        request = message.json()
        corr_id = message.correlation_id
        d("%s: request %s", corr_id, request)

        # HACK: Send a "ping" reply so we don't spend time
        # generating responses that won't be received.
        channel._publish_direct(
            message={"status": "received"},
            routing_key=message.reply_to,
            exchange="",
            correlation_id=corr_id,
        )

        start_time = time.time()

        request_text = self.tokenizer.apply_chat_template(
            request["messages"],
            tokenize=False,
            add_generation_prompt=True,
        )

        model_inputs = self.tokenizer(
            [request_text],
            return_tensors="pt"
        ).to(self.model.device)

        d("%s: model input: %s", corr_id, model_inputs.input_ids.tolist()[0])

        model_output_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=request.get("max_new_tokens", 512),
        )

        generated_ids = [
            output_ids[len(input_ids):]
            for input_ids, output_ids in zip(
                    model_inputs.input_ids,
                    model_output_ids,
            )
        ]

        d("%s: model output: %s", corr_id, generated_ids[0].tolist())

        response_text = self.tokenizer.batch_decode(
            generated_ids,
            skip_special_tokens=True,
        )[0]

        elapsed_time = time.time() - start_time
        num_prompt_tokens = model_inputs.input_ids.shape[1]
        num_completion_tokens = len(generated_ids[0])

        response = {
            "message": {
                "role": "assistant",
                "content": response_text
            },
            "usage": {
                "prompt_tokens": num_prompt_tokens,
                "completion_tokens": num_completion_tokens,
                "total_tokens": num_prompt_tokens + num_completion_tokens,
                "time_seconds": elapsed_time,
            },
        }

        d("%s: response: %s", corr_id, response)
        return response

    def run(self):
        with self.blocking_connection() as conn:
            channel = conn.channel()
            channel.consume_rpc_requests(
                queue=self.request_queue,
                on_message_callback=self.on_request,
            )
            channel.start_consuming()
