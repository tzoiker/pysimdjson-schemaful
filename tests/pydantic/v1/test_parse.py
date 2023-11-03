import re
from json import dumps
from typing import Dict, List, Union

import pytest
from pydantic import ValidationError

from simdjson_schemaful.pydantic.v1 import parse_raw_simdjson_as
from tests.pydantic.v1.conftest import Model, ModelNested


def test_union_fail():
    model = Union[str, Model]
    data = dumps({"some": 0, "value": 1})
    with pytest.raises(
        ValidationError,
        match=re.escape(
            "2 validation errors for ParsingModel[Union[str, Model]]\n__root__\n  "
            "str type expected (type=type_error.str)\n__root__ -> some\n  extra fields "
            "not permitted (type=value_error.extra)"
        ),
    ):
        parse_raw_simdjson_as(model, data)


def test_dict_model_value_ok():
    model = Dict[str, Model]
    data = dumps({"key": {"some": 0, "value": 1}})
    assert parse_raw_simdjson_as(model, data)


def test_nested_dict_model_value_ok():
    model = List[Dict[str, Model]]
    data = dumps([{"key": {"some": 0, "value": 1}}])
    assert parse_raw_simdjson_as(model, data)


def test_not_an_object():
    model = dict
    data = dumps("abc")
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Supposed to be an object, but in reality is a <class 'str'>",
        ),
    ):
        parse_raw_simdjson_as(model, data)


def test_nested_not_an_object():
    model = List[dict]
    data = dumps(["abc"])
    with pytest.raises(
        ValueError,
        match=re.escape("Supposed to be an object, but in reality is a <class 'str'>"),
    ):
        parse_raw_simdjson_as(model, data)


def test_not_an_array():
    model = list
    data = dumps("abc")
    with pytest.raises(
        ValueError,
        match=re.escape("Supposed to be an array, but in reality is a <class 'str'>"),
    ):
        parse_raw_simdjson_as(model, data)


def test_nested_not_an_array():
    model = List[list]
    data = dumps(["abc"])
    with pytest.raises(
        ValueError,
        match=re.escape("Supposed to be an array, but in reality is a <class 'str'>"),
    ):
        parse_raw_simdjson_as(model, data)


def test_ok():
    data = [
        {
            "l1_list": [
                {
                    "l2": {"s": "0", "i": 0, "f": 0.0, "other": "value"},
                    "l2_model_values": {
                        "some": {"s": "0", "i": 0, "f": 0.0, "other": "value"},
                        "other": {"s": "1", "i": 1, "f": 1.0, "other": "value"},
                    },
                },
                {"l2": {"s": "1", "i": 1, "f": 1.0, "another": "value"}},
            ],
        }
    ]
    expected = [
        {
            "l1_list": [
                {
                    "l2": {"s": "0", "i": 0, "f": 0.0},
                    "l2_model_values": {
                        "some": {"s": "0", "i": 0, "f": 0.0},
                        "other": {"s": "1", "i": 1, "f": 1.0},
                    },
                },
                {"l2": {"s": "1", "i": 1, "f": 1.0}},
            ],
        }
    ]
    (parsed,) = parse_raw_simdjson_as(List[ModelNested], dumps(data))
    assert [parsed.dict(exclude_none=True)] == expected


def test_raw_missing_required():
    data = {
        "l1_list": [
            {"l2": {"s": "0", "i": 0}},
        ],
    }
    with pytest.raises(
        ValidationError,
        match=re.escape(
            "1 validation error for ParsingModel[ModelNested]\n__root__ -> l1_list "
            "-> 0 -> l2 -> f\n  field required (type=value_error.missing)"
        ),
    ):
        parse_raw_simdjson_as(ModelNested, dumps(data))
