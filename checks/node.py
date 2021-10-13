from skale.utils.helper import ip_from_bytes
from skale.utils.web3_utils import public_key_to_address

from checks.watchdog import WatchdogChecks


class NodeChecks(WatchdogChecks):
    def __init__(self, skale, node_id, domain_name=None, network='mainnet'):
        self.skale = skale
        self.node = self.skale.nodes.get(node_id)
        self.node['ip'] = ip_from_bytes(self.node['ip'])
        self.node['address'] = public_key_to_address(self.node['publicKey'])
        super().__init__(self.node['ip'], domain_name=domain_name, network=network,
                         web3=self.skale.web3)

    def status(self):
        pass

    def balance(self):
        pass

    def validator_balance(self):
        pass

    def logs(self):
        pass
