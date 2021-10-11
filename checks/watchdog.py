from watchdog.client import Watchdog


class WatchdogChecks:
    def __init__(self, node_ip, domain_name=None):
        self.watchdog = Watchdog(node_ip)
        self.domain_name = domain_name

    def get(self, *checks):
        check_results = {}
        for check in checks:
            check_results[check] = self.__getattribute__(check)()
        return check_results

