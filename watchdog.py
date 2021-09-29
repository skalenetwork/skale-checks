import requests


WATCHDOG_TIMEOUT_DEFAULT = 10
WATCHDOG_PORT = 3009


class WatchdogConnectionError(Exception):
    pass


class WatchdogClient:
    def __init__(self, node_ip, timeout=WATCHDOG_TIMEOUT_DEFAULT):
        self.watchdog = WatchdogServer(node_ip, timeout)


class WatchdogServer:
    def __init__(self, node_ip, timeout=WATCHDOG_TIMEOUT_DEFAULT):
        self.ip = node_ip
        self.timeout = timeout
        self.watchdog_url = get_watchdog_url(node_ip)

    def __send_request(self, path, raw_json=False):
        try:
            url = f'{self.watchdog_url}{path}'
            response = requests.get(url=url, timeout=self.timeout)
            response.raise_for_status()
            raw_data = response.json()
            if raw_json:
                return raw_data
            return raw_data['data']
        except requests.exceptions.RequestException as e:
            raise WatchdogConnectionError(e)


def get_watchdog_url(node_ip):
    return f'http://{node_ip}:{WATCHDOG_PORT}'
