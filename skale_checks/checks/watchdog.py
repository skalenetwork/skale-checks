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

import re
from datetime import datetime
import datetime as dt

from skale_checks.adapters.watchdog import Watchdog
from skale_checks.checks.base import check, BaseChecks
from skale_checks.checks.types import OptionalBool, OptionalBoolTuple

CONTAINER_RUNNING_STATUS = 'running'


class WatchdogChecks(BaseChecks):
    def __init__(self, node_ip, network='mainnet', domain_name=None, web3=None, timeout=None):
        self.node_ip = node_ip
        if timeout:
            self.watchdog = Watchdog(node_ip, timeout=timeout)
        else:
            self.watchdog = Watchdog(node_ip)
        self.domain_name = domain_name
        self.web3 = web3
        super().__init__(network)

    @check(['core'])
    def core(self) -> OptionalBool:
        components = self.watchdog.get_skale_containers()
        if not components.is_status_ok():
            return None
        components = components.payload
        container_statuses = True
        for name in components:
            if name in self.requirements['versions'].keys():
                if components[name]['status'] != CONTAINER_RUNNING_STATUS:
                    container_statuses = False
        return container_statuses

    @check(['endpoint', 'trusted_endpoint', 'endpoint_speed'])
    def endpoint(self) -> OptionalBoolTuple:
        endpoint_response = self.watchdog.endpoint_status()
        if not endpoint_response.is_status_ok():
            return None, None, None
        endpoint_data = endpoint_response.payload
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
        components_response = self.watchdog.get_component_versions()
        if not components_response.is_status_ok():
            return None
        components = components_response.payload
        component_versions = True
        for name in components:
            if name in self.requirements['versions'].keys():
                if components[name] not in self.requirements['versions'][name]:
                    component_versions = False
        return component_versions

    @check(['sgx', 'sgx_version'])
    def sgx(self) -> OptionalBoolTuple:
        sgx_response = self.watchdog.sgx_status()
        if not sgx_response.is_status_ok():
            return None, None
        sgx_data = sgx_response.payload
        is_sgx_working = sgx_data['status'] == 0
        sgx_version_check = sgx_data['sgx_wallet_version'] in self.requirements['versions']['sgx']
        return is_sgx_working, sgx_version_check

    @check(['hardware'])
    def hardware(self) -> OptionalBool:
        hardware_response = self.watchdog.hardware_status()
        if not hardware_response.is_status_ok():
            return None
        hardware_data = hardware_response.payload
        hardware_check = True
        for key in self.requirements['hardware'].keys():
            if hardware_data[key] < self.requirements['hardware'][key]:
                hardware_check = False
        return hardware_check

    @check(['btrfs'])
    def btrfs(self) -> OptionalBool:
        btrfs_response = self.watchdog.btrfs_status()
        if not btrfs_response.is_status_ok():
            return None
        return btrfs_response.payload['kernel_module']

    @check(['public_ip'])
    def public_ip(self) -> OptionalBool:
        public_ip_response = self.watchdog.public_ip()
        if not public_ip_response.is_status_ok():
            return None
        return public_ip_response.payload['public_ip'] == self.node_ip

    @check(['validator_nodes'])
    def validator_nodes(self) -> OptionalBool:
        validator_nodes_response = self.watchdog.validator_nodes()
        if not validator_nodes_response.is_status_ok():
            return None
        validator_nodes = validator_nodes_response.payload
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
        ssl_response = self.watchdog.ssl_status()
        if not ssl_response.is_status_ok():
            return None
        ssl_data = ssl_response.payload
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
