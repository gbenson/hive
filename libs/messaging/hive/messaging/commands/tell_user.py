from hive.common import ArgumentParser

from .. import tell_user


class TellUserArgumentParser(ArgumentParser):
    def add_format_argument(self, format: str, default: str = "text"):
        help = f'send messages as format "{format.upper()}"'
        if format == default:
            help = f"{help} [the default if no format is specified]"
        self.add_argument(
            f"--{format}",
            action="store_const",
            dest="format", default=default, const=format,
            help=help,
        )


def main():
    parser = TellUserArgumentParser(
        description="Post messages to Hive's Matrix room.",
    )
    parser.add_argument(
        "message", metavar="MESSAGE",
        help="message to post"
    )
    for format in ("text", "html", "markdown", "code", "emojize"):
        parser.add_format_argument(format)
    args = parser.parse_args()

    tell_user(args.message, format=args.format)
