# skale-checks
Python package for node and schain checks

## Requirements

* Python 3.7+ compatible

## Installation

```bash
pip install skale-checks
```

## Node checks

Get checks for node on the network, including contract checks and watchdog checks.

```python
from skale_checks.checks.node import NodeChecks

node_checks = NodeChecks(skale, 
                         node_id, 
                         network='mainnet',
                         es_credentials=(ES_ENDPOINT, ES_LOGIN, ES_PASSWORD),
                         timeout=10)
results = node_checks.get()
```

* `skale` - instance of skale
* `node_id` - id od the node to check
* `network` - `mainnet` | `testnet`, `mainnet` by default, **optional**
* `es_credentials` - tuple of elasticsearch endpoint, login and password, **optional**
* `timeout` - watchdog checks timeout, 10 by default, **optional** 

## Watchdog checks

Get checks from specific watchdog. Collect all checks from remote node instance

```python
from skale_checks.checks.watchdog import WatchdogChecks

wd_checks = WatchdogChecks(ip, 
                           network='testnet', 
                           domain_name=None, 
                           web3=None, 
                           timeout=None)
results = wd_checks.get()
```

* `ip` - node ip with watchdog
* `network` - `mainnet` | `testnet`, `mainnet` by default, **optional**
* `domain_name` - node domain name (for ssl check), **optional**
* `web3` - Web3 instance (for endpoint check), **optional**
* `timeout` - connection timeout for watchdog, **optional**
