import inspect
from enum import Enum
from functools import wraps, partial
from checks.utils import get_requirements


def check(result_headers):
    def real_decorator(checker):
        checker.is_check = True

        @wraps(checker)
        def wrapper(*args, **kwargs):
            results = checker(*args, **kwargs)
            if not isinstance(results, tuple):
                results = [results]
            wrapped_results = [
                CheckStatus.UNKNOWN if result is None else CheckStatus(result)
                for result in results
            ]
            return dict(zip(result_headers, wrapped_results))
        return wrapper
    return real_decorator


class CheckStatus(Enum):
    FAILED = 0
    PASSED = 1
    UNKNOWN = 2


class BaseChecks:
    def __init__(self, network='mainnet'):
        self.requirements = get_requirements(network)

    def get(self, *checks):
        check_results = {}
        if len(checks) == 0:
            methods = inspect.getmembers(
                type(self),
                predicate=lambda m: inspect.isfunction(m) and getattr(m, 'is_check', None)
            )
            for method in methods:
                check_results.update(partial(method[1], self)())
        else:
            for check in checks:
                try:
                    item = self.__getattribute__(check)
                    assert hasattr(item, 'is_check')
                    result = item()
                    check_results.update(result)
                except (AttributeError, AssertionError):
                    raise AttributeError(f'Check {check} is not found in WatchdogChecks')
        return check_results
