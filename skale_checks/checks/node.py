#   -*- coding: utf-8 -*-
#
#   This file is part of skale-checks
#
#   Copyright (C) 2021-Present SKALE Labs
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import warnings

from elasticsearch import Elasticsearch, ElasticsearchException
from eth_utils import to_wei
from skale.contracts.manager.nodes import NodeStatus
from skale.utils.helper import ip_from_bytes
from skale.utils.web3_utils import public_key_to_address
from web3 import Web3

from skale_checks.checks.base import check
from skale_checks.checks.types import OptionalBool
from skale_checks.checks.utils import get_active_nodes_count
from skale_checks.checks.watchdog import WatchdogChecks
warnings.filterwarnings("ignore")


class NodeChecks(WatchdogChecks):
    def __init__(self, skale, node_id, network='mainnet', es_credentials=None, timeout=None,
                 logs_timeout=None):
        self.skale = skale
        self.node = self.skale.nodes.get(node_id)
        self.node['id'] = node_id
        self.node['ip'] = ip_from_bytes(self.node['ip'])
        self.es_credentials = es_credentials
        self.logs_timeout = logs_timeout
        super().__init__(self.node['ip'], network=network, domain_name=self.node['domain_name'],
                         web3=self.skale.web3, timeout=timeout)

    @check(['status'])
    def status(self) -> bool:
        return self.node['status'] == NodeStatus.ACTIVE.value

    @check(['node_balance'])
    def node_balance(self) -> bool:
        address = public_key_to_address(self.node['publicKey'])
        node_balance = self.skale.web3.eth.getBalance(Web3.toChecksumAddress(address))
        required_node_balance = to_wei(self.requirements['single_node_balance'], 'ether')
        return required_node_balance <= node_balance

    @check(['val_balance'])
    def validator_balance(self) -> bool:
        active_nodes_count = get_active_nodes_count(self.skale, self.node['validator_id'])
        validator_node_balance_wei = to_wei(self.requirements['validator_node_balance'], 'ether')
        required_validator_balance = active_nodes_count * validator_node_balance_wei

        validator_balance = self.skale.wallets.get_validator_balance(self.node['validator_id'])
        return validator_balance >= required_validator_balance

    @check(['logs'])
    def logs(self) -> OptionalBool:
        es_args = {}
        try:
            if not self.es_credentials or len(self.es_credentials) != 3:
                return None
            if self.logs_timeout:
                es_args = {
                    'timeout': self.logs_timeout,
                    'max_retries': 3,
                    'retry_on_timeout': True
                }
            es = Elasticsearch(self.es_credentials[0],
                               http_auth=self.es_credentials[1:3],
                               **es_args)
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
            return False
