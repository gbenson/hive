from collections import namedtuple
from dataclasses import dataclass

from nacl.public import PrivateKey, PublicKey
from nacl.encoding import Base64Encoder

# We purposefully use different encodings for public and private keys
# to try and avoid ever mixing them up and accidentally disclosing a
# private key by putting it somewhere a public key should go so it
# ends up getting printed out or whatever.

Prefix = namedtuple("Prefix", ("decoded", "encoded"))


class Encoder(Base64Encoder):
    pass


@dataclass
class Encoding:
    first_byte: Prefix

    def encode(self, data: bytes) -> bytes:
        decoded = self.first_byte.decoded + data
        encoded = Encoder.encode(decoded)
        assert encoded.startswith(self.first_byte.encoded)
        return encoded

    def decode(self, data: bytes) -> bytes:
        if not data.startswith(self.first_byte.encoded):
            raise ValueError
        decoded = Encoder.decode(data)
        assert decoded.startswith(self.first_byte.decoded)
        return decoded[1:]


# As the first byte of a triplet,
# 0xe0..0xe3 encode to base64 as "4...", and
# 0xf0..0xf3 encode to base64 as "8...",
# so treat bit 0x10 as denoting private/public.
_NACL_ASYMMETRIC_PUBLIC_KEY_V1 = Encoding(Prefix(b"\xe0", b"4"))
_NACL_ASYMMETRIC_PRIVATE_KEY_V1 = Encoding(Prefix(b"\xf0", b"8"))


class KeyEncoder(Encoder):
    pass


class PublicKeyEncoder(KeyEncoder):
    @staticmethod
    def type_check(key):
        if not isinstance(key, PublicKey):
            raise TypeError(type(key))

    @staticmethod
    def encode(data: bytes) -> bytes:
        return _NACL_ASYMMETRIC_PUBLIC_KEY_V1.encode(data)

    @staticmethod
    def decode(data: bytes) -> bytes:
        return _NACL_ASYMMETRIC_PUBLIC_KEY_V1.decode(data)


class PrivateKeyEncoder(KeyEncoder):
    @staticmethod
    def type_check(key):
        if not isinstance(key, PrivateKey):
            raise TypeError(type(key))

    @staticmethod
    def encode(data: bytes) -> bytes:
        return _NACL_ASYMMETRIC_PRIVATE_KEY_V1.encode(data)

    @staticmethod
    def decode(data: bytes) -> bytes:
        return _NACL_ASYMMETRIC_PRIVATE_KEY_V1.decode(data)


def encode_public_key(key: PublicKey) -> str:
    return _encode_key(key, PublicKeyEncoder)


def encode_private_key(key: PrivateKey) -> str:
    return _encode_key(key, PrivateKeyEncoder)


def _encode_key(key: PublicKey | PrivateKey, encoder: KeyEncoder) -> str:
    encoder.type_check(key)
    return key.encode(encoder=encoder).decode("ascii")


def decode_public_key(s: str):
    return PublicKey(s.encode("ascii"), encoder=PublicKeyEncoder)


def decode_private_key(s: str):
    return PrivateKey(s.encode("ascii"), encoder=PrivateKeyEncoder)
