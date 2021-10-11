import requests

DEFAULT_TIMEOUT = 10
ERROR_STATUS = 'error'
OK_STATUS = 'ok'


class Connector:
    def __init__(self, ip, timeout=DEFAULT_TIMEOUT):
        self.ip = ip
        self.timeout = timeout

    def send_request(self, path):
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


def construct_ok_response(data=None):
    if data is None:
        data = {}
    return {'status': 'ok', 'payload': data}


def construct_err_response(msg=None):
    if msg is None:
        msg = {}
    return {'status': 'error', 'payload': msg}


def is_status_ok(data):
    return data['status'] == OK_STATUS