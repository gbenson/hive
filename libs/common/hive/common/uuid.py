from hashlib import blake2b
from uuid import RFC_4122, UUID


def parse_uuid(uuid: str | UUID) -> UUID:
    if not isinstance(uuid, UUID):
        uuid = UUID(uuid)

    if uuid.variant != RFC_4122:
        raise ValueError(uuid)
    if uuid.version != 4:
        raise ValueError(uuid)

    return uuid


def blake2b_digest_uuid(data: str | bytes) -> UUID:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return UUID(bytes=blake2b(data, digest_size=16).digest(), version=4)
