from nacl.public import PrivateKey, PublicKey

from hive.crypto import decode_private_key, decode_public_key
from hive.crypto.keygen import main


def test_keygen(capsys):
    main()
    captured = capsys.readouterr()
    assert not captured.err
    lines = captured.out.split("\n")
    assert len(lines) == 3
    assert lines[2] == ""
    check, encoded_public_key = lines[0].split(":  ")
    assert encoded_public_key[0] == "4"
    assert check == "public_key"
    check, encoded_private_key = lines[1].split(": ")
    assert check == "private_key"
    assert encoded_private_key[0] == "8"

    public_key = decode_public_key(encoded_public_key)
    assert isinstance(public_key, PublicKey)

    private_key = decode_private_key(encoded_private_key)
    assert isinstance(private_key, PrivateKey)
