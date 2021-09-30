import requests

DEFAULT_TIMEOUT = 10


class Server:
    def __init__(self, ip, timeout=DEFAULT_TIMEOUT):
        self.ip = ip
        self.timeout = timeout

    def send_request(self, path):
        try:
            url = f'{self.ip}{path}'
            response = requests.get(url=url, timeout=self.timeout)
            response.raise_for_status()
            raw_data = response.json()
            return construct_ok_response(raw_data)
        except requests.exceptions.RequestException as e:
            return construct_err_response(msg=e)


def construct_ok_response(data=None):
    if data is None:
        data = {}
    return {'status': 'ok', 'payload': data}


def construct_err_response(msg=None):
    if msg is None:
        msg = {}
    return {'status': 'error', 'payload': msg}