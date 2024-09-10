from collections.abc import Iterable

from nacl.public import PublicKey

from .encoding import decode_private_key, decode_public_key


class Endpoint:
    def __init__(self, private_key: str, authorized_keys: Iterable[str]):
        self._private_key = decode_private_key(private_key)
        self._authorized_keys = dict(
            (bytes(public_key), public_key)
            for public_key in map(decode_public_key, public_keys)
        )

    def encrypt_to(self, data: bytes, receiver: PublicKey):
        raise NotImplementedError

    def decrypt(self, data: bytes):
        raise NotImplementedError

    def decrypt_from(self, data: bytes, sender: PublicKey):
        raise NotImplementedError
