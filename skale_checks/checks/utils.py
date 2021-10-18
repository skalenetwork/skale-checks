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
from skale_checks.checks import REQUIREMENTS_FILE
from concurrent.futures import ThreadPoolExecutor


def get_requirements(network='mainnet'):
    with open(REQUIREMENTS_FILE, 'r') as stream:
        try:
            all_requirements = yaml.safe_load(stream)
            return all_requirements[network]
        except yaml.YAMLError as exc:
            print(exc)


def get_active_nodes_count(skale, validator_id):
    validator_node_ids = skale.nodes.get_validator_node_indices(validator_id)
    executor = ThreadPoolExecutor(max_workers=len(validator_node_ids))
    res = executor.map(skale.nodes.is_node_active, validator_node_ids)
    return sum(res)
