from functools import wraps

from checks.utils import get_requirements


def watchdog_check(fields):
    def real_decorator(checker):
        checker.is_check = True
        @wraps(checker)
        def wrapper(*args, **kwargs):
            results = checker(*args, **kwargs)
            if not isinstance(results, tuple):
                results = [results]
            return dict(zip(fields, results))
        return wrapper
    return real_decorator



class BaseChecks:
    def __init__(self, network='mainnet'):
        self.requirements = get_requirements(network)

    def get(self, *checks):
        check_results = {}
        for check in checks:
            try:
                res = self.__getattribute__(check)()
                check_results.update(res)
            except AttributeError:
                raise AttributeError(f'Check {check} is not found')
        return check_results
