import os

import pytest

from pika import PlainCredentials

from hive.common.testing import test_config_dir  # noqa: F401
from hive.messaging import DEFAULT_MESSAGE_BUS


@pytest.fixture
def real_credentials():
    try:
        return DEFAULT_MESSAGE_BUS.credentials
    except KeyError:
        return None


@pytest.fixture
def test_credentials(real_credentials, test_config_dir):  # noqa: F811
    """Write an `rabbitmq.env` file where `MessageBus.credentials`
    will read it.  If credentials were already provided, those
    are used; otherwise the defaults (`("guest", "guest")`) are
    used.
    """
    creds = real_credentials or PlainCredentials("guest", "guest")
    with open(os.path.join(test_config_dir, "rabbitmq.env"), "w") as fp:
        for attr in ("username", "password"):
            key = f"RABBITMQ_DEFAULT_{attr[:4].upper()}"
            value = getattr(creds, attr)
            print(f"{key}={value}", file=fp)
    return DEFAULT_MESSAGE_BUS.credentials
