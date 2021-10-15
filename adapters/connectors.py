from dataclasses import dataclass
from typing import NamedTuple

import requests

DEFAULT_TIMEOUT = 10


@dataclass
class Response():
    status: str
    payload: dict

    ERROR_STATUS = 'error'
    OK_STATUS = 'ok'


class Connector:
    def __init__(self, ip, timeout=DEFAULT_TIMEOUT):
        self.ip = ip
        self.timeout = timeout

    def send_request(self, path) -> Response:
        try:
            url = f'{self.ip}{path}'
            response = requests.get(url=url, timeout=self.timeout)
            response.raise_for_status()
            raw_data = response.json()
            if raw_data['error']:
                return construct_err_response(raw_data['error'])
            return construct_ok_response(raw_data['data'])
        except requests.exceptions.RequestException as msg:
            return construct_err_response(msg=str(msg))


def construct_ok_response(data=None) -> Response:
    if data is None:
        data = {}
    return Response(Response.OK_STATUS, data)


def construct_err_response(msg=None) -> Response:
    if msg is None:
        msg = {}
    return Response(Response.ERROR_STATUS, msg)


def is_status_ok(data) -> bool:
    return data.status == Response.OK_STATUS
