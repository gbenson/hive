from hive.matrix_connector.receiver import main


def test_import():
    assert callable(main)
