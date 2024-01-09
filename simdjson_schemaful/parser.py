from typing import Any, Callable, Dict, List, Optional, Union

import simdjson
from simdjson import Parser

JsonType = Union[Dict[Any, Any], List[Any], str, int, float, bool]
Schema = Dict[Any, Any]
_Dict = Dict[Any, Any]
_List = List[Any]
_FuncSet = Callable[..., None]


# TODO: handle anyOf?


def _get_definition(definitions: Dict[str, Schema], schema: Schema) -> Schema:
    if ref := schema.get("$ref"):
        return definitions[ref.split("/")[-1]]
    return schema


def _set_dict(target: _Dict, key: str, value: Any) -> None:
    target[key] = value


def _set_list(target: _List, index: int, value: Any) -> None:
    if len(target) <= index:
        target.extend([None] * (index + 1 - len(target)))
    target[index] = value


def _process_prop(
    *,
    prop_data: _Dict,
    prop: Union[str, int],
    value: Any,
    target: Union[_Dict, _List],
    func_set: _FuncSet,
    definitions: Schema,
    queue: _List,
) -> None:
    if value is None:
        target[prop] = value  # type: ignore
        return

    type_ = prop_data.get("type")
    items = prop_data.get("items", {})

    if type_ == "array" and not items.get("$ref") and not items.get("properties"):
        if not isinstance(value, simdjson.Array):
            raise ValueError(
                f"Supposed to be an array, but in reality is a {value.__class__}",
            )
        func_set(target, prop, value.as_list())
        return

    if (not type_ and not prop_data.get("$ref")) or (
        type_ == "object"
        and not prop_data.get("properties")
        and not prop_data.get("additionalProperties")
    ):
        if not isinstance(value, simdjson.Object):
            raise ValueError(
                f"Supposed to be an object, but in reality is a {value.__class__}",
            )
        func_set(target, prop, value.as_dict())
        return

    if type_ not in (None, "array", "object"):
        if isinstance(value, (simdjson.Object, simdjson.Array)):
            raise ValueError(
                f"Supposed to be anything but object/array, "
                f"but in reality is {value.__class__}",
            )
        func_set(target, prop, value)
        return

    if type_ == "array":
        definition = prop_data
        func_set(target, prop, [])
    elif type_ == "object" or prop_data.get("$ref"):
        definition = _get_definition(definitions, prop_data)
        func_set(target, prop, {})
    else:
        raise ValueError(f"invalid type {type_} for prop data {prop_data}")

    queue.append((definition, value, target[prop]))  # type: ignore


def _loads(  # noqa: C901
    data: Union[bytes, bytearray, memoryview],
    *,
    schema: Schema,
    parser: Parser,
) -> JsonType:
    definitions = schema.get("definitions", {}) or schema.get("$defs", {})

    if "$ref" in schema:
        schema = _get_definition(definitions, schema)

    type_ = schema.get("type")
    if type_ not in ["object", "array"]:
        return simdjson.loads(data)  # type: ignore

    res: Union[_List, _Dict] = {} if type_ == "object" else []

    source = parser.parse(data)
    target = res
    queue = [(schema, source, target)]

    while queue:
        schema, source, target = queue.pop()
        type_ = schema["type"]

        if type_ == "object":
            if not isinstance(source, simdjson.Object):
                raise ValueError(
                    f"Supposed to be an object, but in reality is a {source.__class__}",
                )

            properties = schema.get("properties", {})

            if properties:
                for prop_name, prop_data in properties.items():
                    value = None
                    try:
                        value = source[prop_name]
                    except KeyError:
                        continue

                    _process_prop(
                        prop_data=prop_data,
                        prop=prop_name,
                        value=value,
                        target=target,
                        func_set=_set_dict,
                        definitions=definitions,
                        queue=queue,
                    )
                continue

            additional_properties = _get_definition(
                definitions=definitions,
                schema=schema.get("additionalProperties", {}),
            )
            if additional_properties:
                for prop_name in source.keys():
                    value = source.get(prop_name)
                    _process_prop(
                        prop_data=additional_properties,
                        prop=prop_name,
                        value=value,
                        target=target,
                        func_set=_set_dict,
                        definitions=definitions,
                        queue=queue,
                    )
                continue

            target.update(source.as_dict())  # type: ignore

        elif type_ == "array":
            if not isinstance(source, simdjson.Array):
                raise ValueError(
                    f"Supposed to be an array, but in reality is a {source.__class__}"
                )

            for i, value in enumerate(source):
                _process_prop(
                    prop_data=_get_definition(definitions, schema["items"]),
                    prop=i,
                    value=value,
                    target=target,
                    func_set=_set_list,
                    definitions=definitions,
                    queue=queue,
                )
        else:
            raise ValueError(f"Invalid schema type {type_}, expected object or array")

    return res


def loads(
    data: Union[str, bytes, bytearray, memoryview],
    *,
    schema: Schema,
    parser: Optional[Parser] = None,
    **_: Any,
) -> JsonType:
    if isinstance(data, str):
        data = data.encode()
    parser = parser or Parser()  # Default for thread safety
    return _loads(data, schema=schema, parser=parser)
