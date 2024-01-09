from typing import TYPE_CHECKING, Any, Dict, Optional, Type, TypeVar, Union

import pydantic
from pydantic import schema_of
from pydantic.error_wrappers import ErrorWrapper, ValidationError
from pydantic.main import ROOT_KEY
from pydantic.tools import NameFactory, parse_obj_as
from simdjson import Parser

from simdjson_schemaful import loads
from simdjson_schemaful.parser import Schema

if TYPE_CHECKING:
    Model = TypeVar("Model", bound="BaseModel")


class ModelMetaclass(pydantic.main.ModelMetaclass):
    def __new__(cls, *args: Any, **kwargs: Any) -> type:
        ret = super().__new__(cls, *args, **kwargs)
        _REGISTRY[ret] = ret.schema()
        return ret


T = TypeVar("T")
_REGISTRY: Dict[ModelMetaclass, Schema] = {}


class BaseModel(pydantic.BaseModel, metaclass=ModelMetaclass):
    @classmethod
    def parse_raw_simdjson(
        cls: Type["Model"],
        b: Union[str, bytes],
        parser: Optional[Parser] = None,
    ) -> "Model":
        try:
            obj = loads(b, schema=_REGISTRY[cls], parser=parser)
        except (ValueError, TypeError, UnicodeDecodeError) as e:
            raise ValidationError([ErrorWrapper(e, loc=ROOT_KEY)], cls)
        return cls.parse_obj(obj)


def parse_raw_simdjson_as(
    type_: Type[T],
    b: Union[str, bytes],
    *,
    parser: Optional[Parser] = None,
    type_name: Optional[NameFactory] = None,
    **_: Any,
) -> T:
    schema = schema_of(type_)  # already cached in pydantic
    obj = loads(b, schema=schema, parser=parser)
    return parse_obj_as(type_, obj, type_name=type_name)
