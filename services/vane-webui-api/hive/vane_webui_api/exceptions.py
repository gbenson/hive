from http import HTTPStatus


class HTTPError(Exception):
    def __init__(self, status: HTTPStatus):
        self.status = status
