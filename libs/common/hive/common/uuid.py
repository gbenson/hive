from uuid import RFC_4122, UUID


def parse_uuid(uuid: str | UUID) -> UUID:
    if not isinstance(uuid, UUID):
        uuid = UUID(uuid)

    if uuid.variant != RFC_4122:
        raise ValueError(uuid)
    if uuid.version != 4:
        raise ValueError(uuid)

    return uuid
