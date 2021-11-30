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
from functools import lru_cache, partial

from skale_checks.adapters.connectors import (Connector, construct_ok_response,
                                              construct_err_response, Response)

WATCHDOG_TIMEOUT_DEFAULT = 10
WATCHDOG_PORT = 3009


class WatchdogConnector(Connector):
    __ROUTES = {
        'core_status': '/status/core',
        'sgx_status': '/status/sgx',
        'hardware_status': '/status/hardware',
        'endpoint_status': '/status/endpoint',
        'schain_containers_versions_status': '/status/schain-containers-versions',
        'meta_status': '/status/meta-info',
        'btrfs_status': '/status/btrfs',
        'ssl_status': '/status/ssl',
        'ima_status': '/status/ima',
        'public_ip': '/status/public-ip',
        'validator_nodes': '/status/validator-nodes',
        'check_report': '/status/check-report',
        'schains_status': '/status/schains'
    }

    def __init__(self, node_ip, timeout=WATCHDOG_TIMEOUT_DEFAULT):
        self.watchdog_url = get_watchdog_url(node_ip)
        self.timeout = timeout
        super().__init__(self.watchdog_url, self.timeout)

    def __getattr__(self, attr):
        return partial(self.__watchdog_call, attr=attr)

    def __watchdog_call(self, attr):
        route = self.__ROUTES.get(attr)
        if not route:
            raise AttributeError(attr)
        return super().send_request(route)


class Watchdog(WatchdogConnector):
    def __init__(self, node_ip, timeout=WATCHDOG_TIMEOUT_DEFAULT):
        super().__init__(node_ip, timeout)

    @lru_cache(maxsize=10)
    def get_skale_containers(self) -> Response:
        containers_response = self.core_status()
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
        schain_versions_response = self.schain_containers_versions_status()
        if not schain_versions_response.is_status_ok():
            return construct_err_response(schain_versions_response.payload)
        meta_response = self.meta_status()
        if not meta_response.is_status_ok():
            return construct_err_response(meta_response.payload)
        versions = {
            name: get_container_version(container['version'])
            for name, container in containers_response.payload.items()
        }
        versions.update({
            'schain': schain_versions_response.payload['skaled_version'],
            'ima': schain_versions_response.payload['ima_version']
        })
        versions.update({
            'node-cli': meta_response.payload['version'],
            'configs': meta_response.payload['config_stream'],
            'docker-lvmpy': meta_response.payload['docker_lvmpy_stream']
        })
        return construct_ok_response(versions)

    def get_schain_status(self, schain_name):
        schains_response = self.schains_status()
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
