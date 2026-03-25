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
import os
import logging

from elasticsearch import Elasticsearch, ElasticsearchException
from enum import IntEnum
from eth_utils import to_wei
from skale.contracts.manager.nodes import NodeStatus
from skale.dataclasses.skaled_ports import SkaledPorts
from skale.schain_config.ports_allocation import get_schain_base_port_on_node
from skale.utils.helper import ip_from_bytes
from skale.utils.web3_utils import public_key_to_address
from web3 import Web3

from skale_checks.checks.base import check
from skale_checks.checks.types import OptionalBool
from skale_checks.checks.utils import get_active_nodes_count, is_port_open
from skale_checks.checks.watchdog import WatchdogChecks

warnings.filterwarnings("ignore")


ENABLE_INGESTION_LAG_CATCHER = os.getenv('ENABLE_INGESTION_LAG_CATCHER', 'False') == 'True'

logger = logging.getLogger(__name__)


MAX_SCHAINS_PER_NODE = 8


class SGXPort(IntEnum):
    HTTPS = 1026
    TLS = 1027
    LOCAL = 1028
    HTTP_ONLY = 1029
    INFO = 1030
    ZMQ = 1031


class NodeChecks(WatchdogChecks):
    def __init__(self, skale, node_id, network='mainnet', es_credentials=None, timeout=None,
                 logs_timeout=None, requirements_path=None):
        self.skale = skale
        self.node = self.skale.nodes.get(node_id)
        self.node['id'] = node_id
        self.node['ip'] = ip_from_bytes(self.node['ip'])
        self.es_credentials = es_credentials
        self.logs_timeout = logs_timeout
        super().__init__(self.node['ip'], network=network, domain_name=self.node['domain_name'],
                         web3=self.skale.web3, timeout=timeout, requirements_path=requirements_path)

    @check(['status'])
    def status(self) -> bool:
        return self.node['status'] == NodeStatus.ACTIVE.value

    @check(['node_balance'])
    def node_balance(self) -> bool:
        address = public_key_to_address(self.node['publicKey'])
        node_balance = self.skale.web3.eth.get_balance(Web3.to_checksum_address(address))
        required_node_balance = to_wei(self.requirements['single_node_balance'], 'ether')
        return required_node_balance <= node_balance

    @check(['val_balance'])
    def validator_balance(self) -> bool:
        active_nodes_count = get_active_nodes_count(self.skale, self.node['validator_id'])
        validator_node_balance_wei = to_wei(self.requirements['validator_node_balance'], 'ether')
        required_validator_balance = active_nodes_count * validator_node_balance_wei

        validator_balance = self.skale.wallets.get_validator_balance(self.node['validator_id'])
        return validator_balance >= required_validator_balance

    @check(['internal_ports'])
    def internal_ports(self) -> bool:
        """ Checks that internal ports are not accessible from the host """
        node_id = self.node['id']
        active_schains_hashes = self.skale.schains_internal.get_active_schain_hashes_for_node(
            node_id)
        schains_hashes = self.skale.schains_internal.get_schain_hashes_for_node(node_id)
        for schain_hash in active_schains_hashes:
            schain_base_port = get_schain_base_port_on_node(
                schains_hashes,
                schain_hash,
                self.node['port']
            )
            for offset_endpoint in [
                SkaledPorts.PROPOSAL.value,
                SkaledPorts.CATCHUP.value,
                SkaledPorts.BINARY_CONSENSUS.value,
                SkaledPorts.ZMQ_BROADCAST.value
            ]:
                try:
                    port = schain_base_port + offset_endpoint
                    if is_port_open(self.node['ip'], port):
                        return False
                except OSError:
                    return False
        sgx_ports = [element.value for element in SGXPort]
        for port in sgx_ports:
            try:
                if is_port_open(self.node['ip'], port):
                    return False
            except OSError:
                return False
        return True

    @check(['logs'])
    def logs(self) -> OptionalBool:
        es_args = {}
        logger.debug('Checking ES logs for node %s', self.node['id'])
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

            gap_seconds = self.requirements.get('logs_gap', 1800)

            query = {
                "size": 0,
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "fields.id": self.node['id']
                                }
                            }
                        ],
                        "filter": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": f"now-{int(gap_seconds)}s"
                                    }
                                }
                            }
                        ]
                    }
                }
            }

            # Search across all indices EXCEPT system indices (which start with a dot)
            # ignore_unavailable=True prevents errors if some indices are closed or deleted
            result = es.search(
                index="*,-.*",
                body=query,
                ignore_unavailable=True
            )

            total_hits = result['hits']['total']['value']

            # ==== INGESTION LAG CATCHER ====
            # Optional diagnostic fallback for intermittent Elasticsearch ingestion lag.
            if ENABLE_INGESTION_LAG_CATCHER and total_hits == 0:
                # Request the most recent log without time restrictions
                debug_query = {
                    "size": 1,
                    "sort": [{"@timestamp": {"order": "desc"}}],
                    "query": {"match": {"fields.id": self.node['id']}}
                }
                try:
                    debug_res = es.search(index="*,-.*", body=debug_query, ignore_unavailable=True)
                    if debug_res['hits']['hits']:
                        last_log_time = debug_res['hits']['hits'][0]['_source'].get('@timestamp')
                        logger.warning(
                            '[%s] LOGS failed: 0 logs in %ss; but latest ES log @timestamp=%s',
                            self.node['id'],
                            gap_seconds,
                            last_log_time,
                        )
                    else:
                        logger.warning(
                            '[%s] LOGS failed: no logs found for this node in current indices',
                            self.node['id'],
                        )
                except Exception as e:
                    logger.warning('[%s] Ingestion lag debug query failed: %s',
                                   self.node['id'],
                                   e)
            # ===============================

            return total_hits > 0

        except (ConnectionError, ElasticsearchException) as e:
            logger.warning('ES network/timeout for node %s: %s', self.node['id'], e)
            return False

        except Exception as e:
            logger.exception('ES critical error for node ID %s: %s', self.node['id'], e)
            return False
