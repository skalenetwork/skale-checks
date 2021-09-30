from server import Server

WATCHDOG_TIMEOUT_DEFAULT = 10
WATCHDOG_PORT = 3009


class WatchdogConnectionError(Exception):
    pass


class WatchdogClient:
    def __init__(self, node_ip, timeout=WATCHDOG_TIMEOUT_DEFAULT):
        self.watchdog = WatchdogServer(node_ip, timeout)


class WatchdogServer(Server):
    def __init__(self, node_ip, timeout=WATCHDOG_TIMEOUT_DEFAULT):
        self.watchdog_url = get_watchdog_url(node_ip)
        self.timeout = timeout
        super().__init__(self.watchdog_url, self.timeout)

    def core_status(self):
        return super().send_request('/status/core')

    def schains_status(self):
        return super().send_request('/status/schains')

    def sgx_status(self):
        return super().send_request('/status/sgx')

    def hardware_status(self):
        return super().send_request('/status/hardware')

    def endpoint_status(self):
        return super().send_request('/status/endpoint')

    def schain_containers_versions_status(self):
        return super().send_request('/status/schain-containers-versions')

    def meta_status(self):
        return super().send_request('/status/meta')

    def btrfs_status(self):
        return super().send_request('/status/btrfs')

    def ssl_status(self):
        return super().send_request('/status/ssl')

    def ima_status(self):
        return super().send_request('/status/ima')

    def public_ip(self):
        return super().send_request('/status/public-ip')

    def validator_nodes(self):
        return super().send_request('/status/validator-nodes')

    def check_report(self):
        return super().send_request('/status/check-report')


def get_watchdog_url(node_ip):
    return f'http://{node_ip}:{WATCHDOG_PORT}'


print(WatchdogServer('18.221.96.190').sgx_status())