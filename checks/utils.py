import yaml
from enum import Enum
from checks import REQUIREMENTS_FILE


class CheckStatus(Enum):
    FAILED = 0
    PASSED = 1
    UNKNOWN = 2


def get_requirements(network='mainnet'):
    with open(REQUIREMENTS_FILE, 'r') as stream:
        try:
            all_requirements = yaml.safe_load(stream)
            return all_requirements[network]
        except yaml.YAMLError as exc:
            print(exc)