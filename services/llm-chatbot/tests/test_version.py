from hive.common.testing import assert_is_valid_version
from hive.llm_chatbot.__version__ import __version__


def test_version():
    assert_is_valid_version(__version__)
