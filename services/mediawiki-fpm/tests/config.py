from hive.common import read_config

_hosts: dict[str, str] = read_config("hostnames")
_paths: dict[str, str] = read_config("mediawiki-paths")

# The hostnames where the wiki is and isn't, respectively.
SERVICE_HOSTNAME = _hosts["SERVICE_HOSTNAME"]
DEFAULT_HOSTNAME = _hosts["DEFAULT_HOSTNAME"]

# The path used to construct short URL prefixes.
#
# For English Wikipedia this would be "wiki", to yield URLs of
# the form <https://en.wikipedia.org/wiki/Amalia_Ulman>.
ARTICLE_PATH = _paths["WG_ARTICLE_PATH"]
SHORT_URL_PREFIX = f"https://{SERVICE_HOSTNAME}/{ARTICLE_PATH}"

# The URL base path to the directory containing the wiki.
#
# For English Wikipedia this would be "w", to yield URLs of the
# form <https://en.wikipedia.org/w/index.php?title=Amalia_Ulman>.
SCRIPT_PATH = _paths["WG_SCRIPT_PATH"]
SCRIPT_URL_PREFIX = f"https://{SERVICE_HOSTNAME}/{SCRIPT_PATH}"

# The URL path to static resources (images, scripts, etc.)
#
# For English Wikipedia this would be "static", for URLs like
# <https://en.wikipedia.org/static/favicon/wikipedia.ico>.
RESOURCE_BASE_PATH = _paths["WG_RESOURCE_BASE_PATH"]
RESOURCE_URL_PREFIX = f"https://{SERVICE_HOSTNAME}/{RESOURCE_BASE_PATH}"
