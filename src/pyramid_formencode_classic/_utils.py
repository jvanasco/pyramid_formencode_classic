from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Type
from typing import Union

# ==============================================================================

from formencode import Schema

SchemaType = Union[Schema, Type[Schema]]
TYPES_ERRORS = Union[str, Dict[Any, Any], Iterable["TYPES_ERRORS"], None]
EncodedErrors = Union[bytes, Dict[Any, Any], List["EncodedErrors"], None]
