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

import yaml
from skale_checks.checks import DEFAULT_REQUIREMENTS_PATH
from concurrent.futures import ThreadPoolExecutor
from web3._utils import request
from importlib import reload


def get_requirements(network='mainnet', requirements_path=None):
    if requirements_path is None:
        requirements_path = DEFAULT_REQUIREMENTS_PATH
    with open(requirements_path, 'r') as stream:
        try:
            all_requirements = yaml.safe_load(stream)
            return all_requirements[network]
        except yaml.YAMLError as exc:
            print(exc)


def is_node_active(skale, node_id):
    reload(request)
    return skale.nodes.is_node_active(node_id)


def get_active_nodes_count(skale, validator_id):
    sum = 0
    validator_node_ids = skale.nodes.get_validator_node_indices(validator_id)
    with ThreadPoolExecutor(max_workers=len(validator_node_ids)) as executor:
        executors_list = [
            executor.submit(is_node_active, skale, id)
            for id in validator_node_ids
        ]
    for executor in executors_list:
        sum += executor.result()
    return sum
