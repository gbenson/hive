try:
    from html2text import html2text  # noqa: F401
except ModuleNotFoundError:
    def html2text(*args, **kwargs):
        raise ModuleNotFoundError("hive-email[html] not installed")
