from importlib.util import find_spec

from pydantic import BaseModel

if find_spec("pydantic.v1"):
    from .v2 import TypeAdapter

    __all__ = (
        "BaseModel",
        "TypeAdapter",
    )
else:
    from .v1 import parse_raw_simdjson_as

    __all__ = (
        "BaseModel",
        "parse_raw_simdjson_as",
    )
