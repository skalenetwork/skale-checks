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
from skale_checks.adapters.connectors import (Connector, construct_ok_response,
                                              construct_err_response, Response)

WATCHDOG_TIMEOUT_DEFAULT = 10
WATCHDOG_PORT = 3009


class WatchdogBase(Connector):
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


class Watchdog(WatchdogBase):
    def __init__(self, node_ip, timeout=WATCHDOG_TIMEOUT_DEFAULT):
        super().__init__(node_ip, timeout)

    def get_skale_containers(self) -> Response:
        containers_response = super().core_status()
        if not containers_response.is_status_ok():
            return construct_err_response(containers_response.payload)
        containers = containers_response.payload
        data = {
            container['name']: {
                'status': container['state']['Status'],
                'exitCode': container['state']['ExitCode'],
                'version': container['image']
            } for container in containers if container['name'].startswith('skale_')
        }
        return construct_ok_response(data)

    def get_component_versions(self):
        containers_response = self.get_skale_containers()
        if not containers_response.is_status_ok():
            return construct_err_response(containers_response.payload)
        schain_versions_response = super().schain_containers_versions_status()
        if not schain_versions_response.is_status_ok():
            return construct_err_response(schain_versions_response.payload)
        meta_response = super().meta_status()
        if not meta_response.is_status_ok():
            return construct_err_response(meta_response.payload)
        versions = {
            name: get_container_version(container['version'])
            for name, container in containers_response.payload.items()
        }
        versions.update(schain_versions_response.payload)
        versions.update(meta_response.payload)
        return construct_ok_response(versions)

    def get_schain_status(self, schain_name):
        schains_response = super().schains_status()
        if not schains_response.is_status_ok():
            return construct_err_response(schains_response.payload)
        for schain in schains_response.payload:
            if schain['name'] == schain_name:
                return construct_ok_response(schain)
        return construct_err_response(f'sChain {schain_name} not found')


def get_watchdog_url(node_ip):
    return f'http://{node_ip}:{WATCHDOG_PORT}'


def get_container_version(image_name):
    return re.search(':(.*)', image_name).group(0)[1:]
