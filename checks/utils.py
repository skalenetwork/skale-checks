import yaml
from checks import REQUIREMENTS_FILE


def get_requirements(network='mainnet'):
    with open(REQUIREMENTS_FILE, 'r') as stream:
        try:
            all_requirements = yaml.safe_load(stream)
            return all_requirements[network]
        except yaml.YAMLError as exc:
            print(exc)
