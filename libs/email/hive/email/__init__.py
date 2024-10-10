from os import PathLike
from typing import BinaryIO, TypeAlias

from .message import Message as EmailMessage

email_from_bytes = EmailMessage.from_bytes
email_from_file = EmailMessage.from_file


Openable: TypeAlias = str | PathLike | int
Readable: TypeAlias = BinaryIO
InMemory: TypeAlias = bytes | bytearray


def load_email(source: Openable | Readable | InMemory) -> EmailMessage:
    """Deserialize an email from a file or byte array.
    """
    if isinstance(source, InMemory):
        return email_from_bytes(source)
    if hasattr(source, "read"):
        return email_from_file(source)
    with open(source, "rb") as fp:
        return email_from_file(fp)
