from threading import Lock

from pyargon2 import hash as argon2_hash

from hive.common import read_config


class Authenticator:
    def __init__(self, config_key: str = "vane-webui"):
        config = read_config(config_key)
        for key in ("username", "password_salt", "password_hash"):
            setattr(self, f"_{key}", config[key])
        self._lock = Lock()

    def authenticate(self, username: str, password: str) -> bool:
        if not isinstance(username, str):
            return False
        if not isinstance(password, str):
            return False
        if username != self._username:
            return False
        with self._lock:
            password_hash = argon2_hash(password, self._password_salt)
        return password_hash == self._password_hash
