from nacl.public import PrivateKey, PublicKey
from nacl.encoding import Base64Encoder


def encode(key: PublicKey | PrivateKey) -> str:
    return key.encode(encoder=Base64Encoder).decode()


def main():
    secret_key = PrivateKey.generate()
    public_key = secret_key.public_key
    print(f"public_key: {encode(public_key)}")
    print(f"secret_key: {encode(secret_key)}")
