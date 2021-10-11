from adapters.client import Watchdog
from adapters.connector import is_status_ok
from checks.utils import get_requirements, CheckStatus

CONTAINER_RUNNING_STATUS = 'running'


def watchdog_check(fields):
    def real_decorator(checker):
        def wrapper(*args, **kwargs):
            results = checker(*args, **kwargs)
            if not isinstance(results, tuple):
                results = [results]
            return dict(zip(fields, results))
        return wrapper
    return real_decorator


class WatchdogChecks:
    def __init__(self, node_ip, domain_name=None, network='mainnet'):
        self.node_ip = node_ip
        self.watchdog = Watchdog(node_ip)
        self.domain_name = domain_name
        self.requirements = get_requirements(network)

    def get(self, *checks):
        check_results = {}
        for check in checks:
            res = self.__getattribute__(check)()
            check_results.update(res)
        return check_results

    @watchdog_check(['sgx', 'sgx_version'])
    def sgx(self):
        sgx_status = self.watchdog.sgx_status()
        if not is_status_ok(sgx_status):
            return CheckStatus.UNKNOWN, CheckStatus.UNKNOWN
        data = sgx_status['payload']
        is_sgx_working = CheckStatus(data['status'] == 0)
        sgx_version_check = CheckStatus(data['sgx_wallet_version'] in
                                        self.requirements['versions']['sgx'])
        return is_sgx_working, sgx_version_check

    @watchdog_check(['btrfs'])
    def btrfs(self):
        btrfs_status = self.watchdog.btrfs_status()
        if not is_status_ok(btrfs_status):
            return CheckStatus.UNKNOWN
        return CheckStatus(btrfs_status['payload']['kernel_module'])

    @watchdog_check(['public_ip'])
    def public_ip(self):
        public_ip_status = self.watchdog.public_ip()
        if not is_status_ok(public_ip_status):
            return CheckStatus.UNKNOWN
        return CheckStatus(public_ip_status['payload']['public_ip'] == self.node_ip)

    @watchdog_check(['hardware'])
    def hardware(self):
        hardware_status = self.watchdog.hardware_status()
        if not is_status_ok(hardware_status):
            return CheckStatus.UNKNOWN
        hardware_check = True
        hardware_data = hardware_status['payload']
        for key in self.requirements['hardware'].keys():
            if hardware_data[key] < self.requirements['hardware'][key]:
                hardware_check = False
        return CheckStatus(hardware_check)

    @watchdog_check(['validator_nodes'])
    def validator_nodes(self):
        validator_nodes_data = self.watchdog.validator_nodes()
        if not is_status_ok(validator_nodes_data):
            return CheckStatus.UNKNOWN
        validator_nodes = validator_nodes_data['payload']
        if len(validator_nodes) == 0:
            return CheckStatus.PASSED
        for node in validator_nodes:
            if node[2] is False:
                return CheckStatus.FAILED
        return CheckStatus.PASSED

    @watchdog_check(['versions'])
    def versions(self):
        components = self.watchdog.get_component_versions()
        if not is_status_ok(components):
            return CheckStatus.UNKNOWN
        components = components['payload']
        component_versions = True
        for name in components:
            if name in self.requirements['versions'].keys():
                if components[name] not in self.requirements['versions'][name]:
                    print(name)
                    component_versions = False
        return CheckStatus(component_versions)

    @watchdog_check(['core'])
    def core(self):
        components = self.watchdog.get_skale_containers()
        if not is_status_ok(components):
            return CheckStatus.UNKNOWN
        components = components['payload']
        container_statuses = True
        for name in components:
            if name in self.requirements['versions'].keys():
                if components[name]['status'] != CONTAINER_RUNNING_STATUS:
                    container_statuses = False
        return CheckStatus(container_statuses)
