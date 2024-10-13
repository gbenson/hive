import os

_topdir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
_testdir = os.path.join(_topdir, "tests")
RESOURCEDIR = os.path.join(_testdir, "resources")


def serialized_email_filenames():
    """Iterator over the filenames of every serialized email in the testsuite.
    """
    for dirpath, dirnames, filenames in os.walk(_testdir):
        for filepath in sorted(
                os.path.join(dirpath, filename)
                for filename in filenames
                if filename.endswith(".eml")):
            yield filepath
