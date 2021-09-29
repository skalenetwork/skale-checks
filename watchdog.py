from functools import wraps

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

    def core_status(self):
        return self.__send_request('/status/core')

    def schains_status(self):
        return self.__send_request('/status/schains')

    def sgx_status(self):
        return self.__send_request('/status/sgx')

    def hardware_status(self):
        return self.__send_request('/status/hardware')

    def endpoint_status(self):
        return self.__send_request('/status/endpoint')

    def schain_containers_versions_status(self):
        return self.__send_request('/status/schain-containers-versions')

    def meta_status(self):
        return self.__send_request('/status/meta')

    def btrfs_status(self):
        return self.__send_request('/status/btrfs')

    def ssl_status(self):
        return self.__send_request('/status/ssl')

    def ima_status(self):
        return self.__send_request('/status/ima')

    def public_ip(self):
        return self.__send_request('/status/public-ip')

    def validator_nodes(self):
        return self.__send_request('/status/validator-nodes')

    def check_report(self):
        return self.__send_request('/status/check-report')

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
