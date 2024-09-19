from argparse import ArgumentParser

from hive import messaging as msgbus


def main():
    parser = ArgumentParser(
        description="Post messages to Hive's Matrix room.",
    )
    parser.add_argument(
        "messages", metavar="TEXT", nargs="+",
        help="messages to post")
    parser.add_argument(
        "-f", "--format", default="text", choices=[
            "text", "html", "markdown", "code", "emojize",
        ],
        help="format of the messages")
    args = parser.parse_args()

    msgbus.send_to_queue("matrix.messages.outgoing", {
        "format": args.format,
        "messages": args.messages,
    })
