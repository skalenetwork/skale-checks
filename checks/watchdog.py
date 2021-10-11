from adapters.client import Watchdog
from adapters.connector import is_status_ok
from checks.utils import get_requirements, CheckStatus


def watchdog_check(fields):
    def real_decorator(checker):
        def wrapper(self, *args, **kwargs):
            results = checker(self, *args, **kwargs)
            return dict(zip(fields, results))
        return wrapper
    return real_decorator


class WatchdogChecks:
    def __init__(self, node_ip, domain_name=None):
        self.watchdog = Watchdog(node_ip)
        self.domain_name = domain_name
        self.requirements = get_requirements()

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
        print(btrfs_status)
        if not is_status_ok(btrfs_status):
            return CheckStatus.UNKNOWN
        if btrfs_status['payload']['kernel_module']:
            return CheckStatus.PASSED
        return CheckStatus.FAILED
