from elasticsearch import Elasticsearch, ElasticsearchException
from eth_utils import to_wei
from skale.contracts.manager.nodes import NodeStatus
from skale.utils.helper import ip_from_bytes
from skale.utils.web3_utils import public_key_to_address

from checks.utils import CheckStatus
from checks.watchdog import WatchdogChecks, watchdog_check


class NodeChecks(WatchdogChecks):
    def __init__(self, skale, node_id, network='mainnet', es_endpoint=None, es_login=None,
                 es_password=None):
        self.skale = skale
        self.node = self.skale.nodes.get(node_id)
        self.node['ip'] = ip_from_bytes(self.node['ip'])
        self.es_endpoint = es_endpoint
        self.es_login = es_login
        self.es_password = es_password
        super().__init__(self.node['ip'], domain_name=self.node['domain_name'],
                         network=network, web3=self.skale.web3)

    @watchdog_check(['status'])
    def status(self):
        return CheckStatus(self.node['status'] == NodeStatus.ACTIVE.name)

    @watchdog_check(['balance'])
    def balance(self):
        address = public_key_to_address(self.node['publicKey'])
        node_balance = self.skale.web3.eth.getBalance(address)
        required_node_balance = to_wei(self.requirements['single_node_balance'], 'ether')
        return CheckStatus(required_node_balance <= node_balance)

    @watchdog_check(['validator'])
    def validator_balance(self):
        validator_node_ids = self.skale.nodes.get_validator_node_indices(self.node['validator_id'])
        active_ids = self.skale.nodes.get_active_node_ids()
        validator_nodes_count = len(list(set(validator_node_ids) & set(active_ids)))

        validator_node_balance_wei = to_wei(self.requirements['validator_node_balance'], 'ether')
        required_validator_balance = validator_nodes_count * validator_node_balance_wei

        validator_balance = self.skale.wallets.get_validator_balance(self.node['validator_id'])
        return CheckStatus(validator_balance >= required_validator_balance)

    @watchdog_check(['logs'])
    def logs(self):
        try:
            if not self.es_endpoint or not self.es_login or not self.es_password:
                return None
            es = Elasticsearch(self.es_endpoint,
                               http_auth=(self.es_login, self.es_password))
            query = {
                'size': 1,
                'sort': {
                    '@timestamp': 'desc'
                },
                'query': {
                    'match': {
                        'fields.id': self.node['id']
                    }
                },
            }
            result = es.search(body=query)
            if result['hits']['total']['value'] == 0:
                return False
            time_query = {
                "size": 1,
                "script_fields": {
                    "now": {
                        "script": "new Date().getTime()"
                    }
                }
            }
            time_response = es.search(body=time_query)
            current_time = time_response['hits']['hits'][0]['fields']['now'][0]
            last_timestamp = result['hits']['hits'][0]['sort'][0]
            delta_time = (current_time - last_timestamp) / 1000
            return delta_time < self.requirements['logs_gap']
        except (ConnectionError, ElasticsearchException):
            return None
