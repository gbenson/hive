from collections.abc import Sequence
from dataclasses import KW_ONLY, dataclass
from functools import cached_property
from html import escape
from typing import Any, Callable, ClassVar, IO, Optional, TypeAlias, TypeVar

from humanize import naturalsize, naturaltime

from ollama import ListResponse

from hive.common import blake2b_digest_uuid, dynamic_cast
from hive.common.ollama import Client
from hive.messaging import Channel

from .exceptions import CommandError
from .schema import Request

Model: TypeAlias = ListResponse.Model

T = TypeVar("T")


@dataclass
class ResponseManager:
    channel: Channel
    request: Request
    _: KW_ONLY
    out: IO[str]
    max_argc: int = 100

    def run(self) -> None:
        try:
            self._run()
        except CommandError as e:
            print(f"<code>⚠️ Error: {escape(str(e))}</code>", file=self.out)

    def _run(self) -> None:
        if (args := self.request.user_input.split(maxsplit=self.max_argc - 1)):
            args[0] = args[0].lower()
        try:
            self.on_main_command(tuple(args))
        except NotImplementedError:
            raise CommandError(f"{' '.join(args[:2])}: not implemented")

    AVAILABLE_COMMANDS: ClassVar[dict[str, str]] = {
        "list": "List models",
        "ps": "List running models",
        "show": "Show information for a model",
        "use": "Use a model for chat",
        "stop": "Stop a running model",
        "embed": "Generate embeddings",
        "help": "Help about any command",
    }

    COMMANDS_ALIASES: ClassVar[dict[str, str]] = {
        "ls": "list",
        **{cmd: cmd for cmd in AVAILABLE_COMMANDS},
    }

    def on_main_command(self, args: Sequence[str]) -> None:
        if len(args) < 2 or args[1] in ("-h", "--help", "help"):
            self.on_help_command(args)
            return
        if args[0] != "ollama":
            raise CommandError(f'unknown command "{args[0]}"')
        if not (command := self.COMMANDS_ALIASES.get(args[1])):
            raise CommandError(f'unknown command "{args[1]}" for {args[0]}"')
        if not (run := getattr(self, f"on_{command}_command", None)):
            raise NotImplementedError
        run(args)

    def print(self, *args: Any, **kwargs: Any) -> None:
        file = kwargs.pop("file", self.out)
        print(*args, file=file, **kwargs)

    def on_help_command(self, args: Sequence[str]) -> None:
        raise NotImplementedError

    @cached_property
    def client(self) -> Client:
        return Client()

    @property
    def models(self) -> Sequence[Model]:
        return dynamic_cast(list, self.client.list()["models"])

    def on_list_command(self, args: Sequence[str]) -> None:
        if len(args) != 2:
            raise NotImplementedError

        print = self.print

        def print_row(*args: str, tag: str = "td") -> None:
            cells = " ".join(
                f"<{tag}>{escape(arg)}</{tag}>"
                for arg in args
            )
            print(f"<tr>{cells}</tr>\n")

        def maybe(f: Callable[[T], Any], x: Optional[T]) -> Any:
            return "—" if x is None else f(x)

        print("<table>")
        print_row("Name", "Size", "Modified", tag="th")
        for model in self.models:
            print_row(
                maybe(str, model.model),
                maybe(naturalsize, model.size),
                maybe(naturaltime, model.modified_at),
            )
        print("</table>")

    def on_use_command(self, args: Sequence[str]) -> None:
        if len(args) != 3:
            raise CommandError(f"usage: {' '.join(args[:2])} MODEL")
        model = args[2]

        models = {model.model for model in self.models}
        if model not in models:
            raise CommandError(f"{model}: no such model")

        event_id = self.request.source.event_id
        room_id = self.request.source.room_id
        self.channel.publish_request(
            routing_key="llm.chatbot.requests",
            type="net.gbenson.hive.llm_chatbot_update_context_request",
            time=self.request.time,
            data={
                "context_id": str(blake2b_digest_uuid(room_id)),
                "message": {
                    "id": str(blake2b_digest_uuid(event_id)),
                    "role": "user",
                    "content": {
                        "type": "use_model_command",
                        "use_model_command": f"ollama:{model}",
                    },
                },
            },
        )
        self.channel.send_reaction("👍", in_reply_to=event_id)
        self.channel.set_user_typing(False)
