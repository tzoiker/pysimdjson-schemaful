import json
from typing import TYPE_CHECKING, Any, Dict, Optional, Type, TypeVar, Union

import pydantic
from pydantic import ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError
from simdjson import Parser

from simdjson_schemaful import loads
from simdjson_schemaful.parser import Schema

if TYPE_CHECKING:
    Model = TypeVar("Model", bound="BaseModel")


class ModelMetaclass(pydantic._internal._model_construction.ModelMetaclass):
    def __new__(cls, *args: Any, **kwargs: Any) -> type:
        ret = super().__new__(cls, *args, **kwargs)
        _REGISTRY[ret] = ret.model_json_schema()  # type: ignore
        return ret


T = TypeVar("T")
_REGISTRY: Dict[ModelMetaclass, Schema] = {}


class BaseModel(pydantic.BaseModel, metaclass=ModelMetaclass):
    @classmethod
    def model_validate_simdjson(
        cls: Type["Model"],
        json_data: Union[str, bytes, bytearray],
        parser: Optional[Parser] = None,
    ) -> "Model":
        try:
            obj = loads(json_data, schema=_REGISTRY[cls], parser=parser)
        except (ValueError, TypeError, UnicodeDecodeError) as e:
            raise ValidationError(e)
        return cls.model_validate(obj)


class TypeAdapter(pydantic.TypeAdapter[T]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._simdjson_schema = self.json_schema()

    def _build_error(self, exc: Exception, data: Union[str, bytes]) -> ValidationError:
        if isinstance(exc, UnicodeDecodeError):
            type_str = "value_error.unicodedecode"
        elif isinstance(exc, json.JSONDecodeError):
            type_str = "value_error.jsondecode"
        elif isinstance(exc, ValueError):
            type_str = "value_error"
        else:
            type_str = "type_error"

        details: InitErrorDetails = {
            "type": PydanticCustomError(type_str, str(exc)),
            "loc": ("__root__",),
            "input": data,
        }
        return ValidationError.from_exception_data(self.core_schema["type"], [details])

    def validate_simdjson(
        self,
        data: Union[str, bytes],
        *,
        strict: Optional[bool] = None,
        context: Optional[Dict[str, Any]] = None,
        parser: Optional[Parser] = None,
    ) -> T:
        try:
            obj = loads(data, schema=self._simdjson_schema, parser=parser)
        except (ValueError, TypeError, UnicodeDecodeError) as e:
            raise self._build_error(e, data)
        return self.validate_python(obj, strict=strict, context=context)
