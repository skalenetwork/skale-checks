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

from enum import Enum
from functools import partial
from typing import TypeVar, Callable, Any, Union, Tuple, Dict, List


class CheckStatus(Enum):
    FAILED = 0
    PASSED = 1
    UNKNOWN = 2


Func = TypeVar('Func', bound=Callable[..., Any])
OptionalBool = Union[bool, None]
OptionalBoolTuple = Tuple[OptionalBool, ...]
ChecksDict = Dict[str, CheckStatus]
CheckRunners = List[Union[partial, Func]]
