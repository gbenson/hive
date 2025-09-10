from uuid import RFC_4122, UUID

import pytest

from hive.common import blake2b_digest_uuid


@pytest.mark.parametrize(
    "input,expect_output",
    (("hello world",
      "e9a804b2-e527-4d36-81d2-ffc0bb023cd6"),
     (b"hello world",
      "e9a804b2-e527-4d36-81d2-ffc0bb023cd6"),
     (b"hello worl",
      "30396305-c67f-4a53-bfa6-fc81edce9d3e"),
     (b"hello worldd",
      "6d2af2b7-6f3c-429a-b45d-9d19bb59adc5"),
     ("$Z7hsFT1nc7y9mrWz0oHtET_3kT1uB1ehMKhT8b1zat8",
      "b5885c20-f5f1-40e9-88b6-9bd47c4ee9ff"),
     ("!RoBDTr33Tfqa27zzGK:matrix.org",
      "63960e88-32d5-4bf6-b951-2b045529e487"),
     ))
def test_blake2b_digest_uuid(input: bytes | str, expect_output: str) -> None:
    output = blake2b_digest_uuid(input)
    assert isinstance(output, UUID)
    assert output.variant == RFC_4122
    assert output.version == 4
    assert str(output) == expect_output
