import os
from glob import glob

import pytest

from hive.email import load_email


def serialized_email_filenames(subdir="resources"):
    testdir = os.path.dirname(__file__)
    return sorted(glob(os.path.join(testdir, subdir, "*.eml")))


@pytest.mark.parametrize("filename", serialized_email_filenames())
def test_load_from_named_file(filename):
    _ = load_email(filename)


@pytest.mark.parametrize("filename", serialized_email_filenames())
def test_load_from_readable(filename):
    with open(filename, "rb") as fp:
        _ = load_email(fp)


@pytest.mark.parametrize("filename", serialized_email_filenames())
def test_load_from_bytes(filename):
    with open(filename, "rb") as fp:
        _ = load_email(fp.read())
