from enum import Enum
from typing import TypeVar, Callable, Any, Union, Tuple, Dict


class CheckStatus(Enum):
    FAILED = 0
    PASSED = 1
    UNKNOWN = 2


Func = TypeVar('Func', bound=Callable[..., Any])
OptionalBool = Union[bool, None]
OptionalBoolTuple = Tuple[OptionalBool, ...]
ChecksDict = Dict[str, CheckStatus]
