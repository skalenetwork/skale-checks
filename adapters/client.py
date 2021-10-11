import re

from adapters.connector import Connector, is_status_ok, construct_ok_response, construct_err_response

WATCHDOG_TIMEOUT_DEFAULT = 10
WATCHDOG_PORT = 3009


class WatchdogConnector(Connector):
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
        return super().send_request('/status/meta-info')

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


class Watchdog(WatchdogConnector):
    def __init__(self, node_ip, timeout=WATCHDOG_TIMEOUT_DEFAULT):
        super().__init__(node_ip, timeout)

    def get_skale_containers(self):
        containers = super().core_status()
        if not is_status_ok(containers):
            return construct_err_response(containers['payload'])
        containers = containers['payload']
        data = {
            container['name']: {
                'status': container['state']['Status'],
                'exitCode': container['state']['ExitCode'],
                'version': container['image']
            } for container in containers if container['name'].startswith('skale_')
        }
        return construct_ok_response(data)

    def get_component_versions(self):
        data = self.get_skale_containers()
        if not is_status_ok(data):
            return construct_err_response(data['payload'])
        schain_data = super().schain_containers_versions_status()
        if not is_status_ok(schain_data):
            return construct_err_response(schain_data['payload'])
        meta_data = super().meta_status()
        if not is_status_ok(meta_data):
            return construct_err_response(meta_data['payload'])
        versions = {
            name: get_container_version(container['version'])
            for name, container in data['payload'].items()
        }
        versions.update(schain_data['payload'])
        versions.update(meta_data['payload'])
        return construct_ok_response(versions)

    def get_schain_status(self, schain_name):
        schains_data = super().schains_status()
        if not is_status_ok(schains_data):
            return construct_err_response(schains_data['payload'])
        for schain in schains_data['payload']:
            if schain['name'] == schain_name:
                return construct_ok_response(schain)
        return construct_err_response(f'sChain {schain_name} not found')


def get_watchdog_url(node_ip):
    return f'http://{node_ip}:{WATCHDOG_PORT}'


def get_container_version(image_name):
    return re.search(':(.*)', image_name).group(0)[1:]
