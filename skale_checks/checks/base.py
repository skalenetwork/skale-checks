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

import inspect
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps, partial
from skale_checks.checks.types import ChecksDict, CheckStatus, Func, CheckRunners
from skale_checks.checks.utils import get_requirements

MAX_WORKERS = 3


def check(result_headers) -> Func:
    def real_decorator(checker):
        checker.is_check = True
        checker.headers = result_headers

        @wraps(checker)
        def wrapper(*args, **kwargs) -> ChecksDict:
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


class BaseChecks:
    def __init__(self, network='mainnet'):
        self.requirements = get_requirements(network)

    @classmethod
    def info(cls):
        checks_info = {}
        checks = inspect.getmembers(
            cls,
            predicate=lambda m: inspect.isfunction(m) and getattr(m, 'is_check', None)
        )
        for method in checks:
            checks_info.update({
                method[0]: method[1].headers
            })
        return checks_info

    def get(self, *checks: str) -> ChecksDict:
        check_results = {}
        check_runners = self.__get_check_runners(*checks)

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(runner)
                for runner in check_runners
            ]
            for future in as_completed(futures):
                result = future.result()
                check_results.update(result)

        return check_results

    def __get_check_runners(self, *checks: str) -> CheckRunners:
        check_runners = []

        if len(checks) == 0:
            methods = inspect.getmembers(
                type(self),
                predicate=lambda m: inspect.isfunction(m) and getattr(m, 'is_check', None)
            )
            for method in methods:
                check_runners.append(partial(method[1], self))
        else:
            for check_name in checks:
                try:
                    method = self.__getattribute__(check_name)
                    assert hasattr(method, 'is_check')
                    check_runners.append(method)
                except (AttributeError, AssertionError):
                    raise AttributeError(f'Check {check_name} is not found in WatchdogChecks')
        return check_runners
