from nacl.public import PrivateKey

from .encoding import encode_private_key, encode_public_key


def main():
    private_key = PrivateKey.generate()
    public_key = private_key.public_key
    print(f"public_key:  {encode_public_key(public_key)}")
    print(f"private_key: {encode_private_key(private_key)}")
