import re
from datetime import datetime
import datetime as dt

from adapters.client import Watchdog
from adapters.connector import is_status_ok
from checks.base import check, BaseChecks, OptionalBool, OptionalBoolTuple

CONTAINER_RUNNING_STATUS = 'running'


class WatchdogChecks(BaseChecks):
    def __init__(self, node_ip, domain_name=None, network='mainnet', web3=None):
        self.node_ip = node_ip
        self.watchdog = Watchdog(node_ip)
        self.domain_name = domain_name
        self.web3 = web3
        super().__init__(network)

    @check(['core'])
    def core(self) -> OptionalBool:
        components = self.watchdog.get_skale_containers()
        if not is_status_ok(components):
            return None
        components = components['payload']
        container_statuses = True
        for name in components:
            if name in self.requirements['versions'].keys():
                if components[name]['status'] != CONTAINER_RUNNING_STATUS:
                    container_statuses = False
        return container_statuses

    @check(['endpoint', 'trusted_endpoint', 'endpoint_speed'])
    def endpoint(self) -> OptionalBoolTuple:
        endpoint_data = self.watchdog.endpoint_status()
        if not is_status_ok(endpoint_data):
            return None, None, None
        endpoint_data = endpoint_data['payload']
        if self.web3:
            current_block = self.web3.eth.blockNumber
            blocks_gap = current_block - endpoint_data['block_number']
            endpoint_status = blocks_gap <= self.requirements['blocks_gap']
        else:
            endpoint_status = None
        trusted_endpoint = endpoint_data['trusted']
        endpoint_speed = endpoint_data['call_speed'] <= self.requirements['call_speed']
        return endpoint_status, trusted_endpoint, endpoint_speed

    @check(['versions'])
    def versions(self) -> OptionalBool:
        components = self.watchdog.get_component_versions()
        if not is_status_ok(components):
            return None
        components = components['payload']
        component_versions = True
        for name in components:
            if name in self.requirements['versions'].keys():
                if components[name] not in self.requirements['versions'][name]:
                    print(name)
                    component_versions = False
        return component_versions

    @check(['sgx', 'sgx_version'])
    def sgx(self) -> OptionalBoolTuple:
        sgx_status = self.watchdog.sgx_status()
        if not is_status_ok(sgx_status):
            return None, None
        data = sgx_status['payload']
        is_sgx_working = data['status'] == 0
        sgx_version_check = data['sgx_wallet_version'] in self.requirements['versions']['sgx']
        return is_sgx_working, sgx_version_check

    @check(['hardware'])
    def hardware(self) -> OptionalBool:
        hardware_status = self.watchdog.hardware_status()
        if not is_status_ok(hardware_status):
            return None
        hardware_check = True
        hardware_data = hardware_status['payload']
        for key in self.requirements['hardware'].keys():
            if hardware_data[key] < self.requirements['hardware'][key]:
                hardware_check = False
        return hardware_check

    @check(['btrfs'])
    def btrfs(self) -> OptionalBool:
        btrfs_status = self.watchdog.btrfs_status()
        if not is_status_ok(btrfs_status):
            return None
        return btrfs_status['payload']['kernel_module']

    @check(['public_ip'])
    def public_ip(self) -> OptionalBool:
        public_ip_status = self.watchdog.public_ip()
        if not is_status_ok(public_ip_status):
            return None
        return public_ip_status['payload']['public_ip'] == self.node_ip

    @check(['validator_nodes'])
    def validator_nodes(self) -> OptionalBool:
        validator_nodes_data = self.watchdog.validator_nodes()
        if not is_status_ok(validator_nodes_data):
            return None
        validator_nodes = validator_nodes_data['payload']
        if len(validator_nodes) == 0:
            return True
        for node in validator_nodes:
            if node[2] is False:
                return False
        return True

    @check(['ssl'])
    def ssl(self) -> OptionalBool:
        if not self.domain_name:
            return None
        ssl_data = self.watchdog.ssl_status()
        if not is_status_ok(ssl_data):
            return None
        ssl_data = ssl_data['payload']
        if ssl_data.get('is_empty') is True:
            return False
        else:
            cert_host = ssl_data.get('issued_to')
            try:
                regexp = re.compile(cert_host[1:])
            except Exception:
                return False
            if not regexp.search(self.domain_name):
                return False
            raw_date = ssl_data.get('expiration_date')
            expiration_date = datetime.strptime(raw_date, '%Y-%m-%dT%H:%M:%S')
            offset = dt.timedelta(weeks=self.requirements['ssl_gap_weeks'])
            min_valid_time = (datetime.now() + offset).timestamp()
            if expiration_date.timestamp() < min_valid_time:
                return False
            return True
