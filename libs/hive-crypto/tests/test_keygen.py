from base64 import b64decode

from nacl.public import PrivateKey, PublicKey
from nacl.encoding import Base64Encoder

from hive.crypto.keygen import main


def test_keygen(capsys):
    main()
    captured = capsys.readouterr()
    assert not captured.err
    lines = captured.out.split("\n")
    assert len(lines) == 3
    assert lines[2] == ""
    check, encoded_public_key = lines[0].split(": ")
    assert check == "public_key"
    check, encoded_private_key = lines[1].split(": ")
    assert check == "secret_key"

    public_key = PublicKey(encoded_public_key, encoder=Base64Encoder)
    assert bytes(public_key) == b64decode(encoded_public_key)

    private_key = PrivateKey(encoded_private_key, encoder=Base64Encoder)
    assert bytes(private_key) == b64decode(encoded_private_key)
    assert public_key == private_key.public_key
