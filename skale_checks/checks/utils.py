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

import socket
import errno
from concurrent.futures import ThreadPoolExecutor

import yaml

from skale_checks.checks import DEFAULT_REQUIREMENTS_PATH


SOCKET_TIMEOUT = 3


def get_requirements(network="mainnet", requirements_path=None):
    if requirements_path is None:
        requirements_path = DEFAULT_REQUIREMENTS_PATH
    with open(requirements_path, "r") as stream:
        try:
            all_requirements = yaml.safe_load(stream)
            return all_requirements[network]
        except yaml.YAMLError as exc:
            print(exc)


def is_node_active(skale, node_id):
    return skale.nodes.is_node_active(node_id)


def get_active_nodes_count(skale, validator_id):
    sum = 0
    validator_node_ids = skale.nodes.get_validator_node_indices(validator_id)
    with ThreadPoolExecutor(max_workers=len(validator_node_ids)) as executor:
        executors_list = [
            executor.submit(is_node_active, skale, id) for id in validator_node_ids
        ]
    for executor in executors_list:
        sum += executor.result()
    return sum


def is_port_open(ip: str, port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(SOCKET_TIMEOUT)
    try:
        result = sock.connect_ex((ip, port))
        if result == 0 or result == errno.ECONNREFUSED:
            return True
        else:
            return False
    except (socket.gaierror, OSError):
        # socket.gaierror: DNS resolution error (e.g., invalid hostname)
        # OSError: Other socket errors like "Host unreachable"
        return False
    finally:
        sock.close()
