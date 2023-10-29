import re
from json import dumps
from typing import Dict, List, Union

import pytest
from pydantic import ValidationError

from simdjson_schemaful.pydantic.v2 import TypeAdapter
from tests.pydantic.v2.conftest import Model, ModelNested


def test_union_fail():
    adapter = TypeAdapter(Union[str, Model])
    data = dumps({"some": 0, "value": 1})
    with pytest.raises(
        ValidationError,
        match=re.escape(
            "2 validation errors for union[str,Model]\nstr\n  Input should be a "
            "valid string [type=string_type, input_value={'some': 0, 'value': 1}, "
            "input_type=dict]"
        ),
    ):
        adapter.validate_simdjson(data)


def test_dict_model_value_fail():
    adapter = TypeAdapter(Dict[str, Model])
    data = dumps({"key": {"some": 0, "value": 1}})
    with pytest.raises(
        ValidationError,
        match=re.escape(
            "1 validation error for dict[str,Model]\nkey.some\n  Extra inputs are "
            "not permitted [type=extra_forbidden, input_value=0, input_type=int]"
        ),
    ):
        adapter.validate_simdjson(data)


def test_nested_dict_model_value_fail():
    adapter = TypeAdapter(List[Dict[str, Model]])
    data = dumps([{"key": {"some": 0, "value": 1}}])
    with pytest.raises(
        ValidationError,
        match=re.escape(
            "1 validation error for list[dict[str,Model]]\n0.key.some\n  Extra "
            "inputs are not permitted [type=extra_forbidden, input_value=0, "
            "input_type=int]"
        ),
    ):
        adapter.validate_simdjson(data)


def test_not_an_object():
    adapter = TypeAdapter(dict)
    data = dumps("abc")
    with pytest.raises(
        ValueError,
        match=re.escape(
            "1 validation error for dict\n__root__\n  Supposed to be an object, but in "
            "reality is a <class 'str'>",
        ),
    ):
        adapter.validate_simdjson(data)


def test_nested_not_an_object():
    adapter = TypeAdapter(List[dict])
    data = dumps(["abc"])
    with pytest.raises(
        ValueError,
        match=re.escape(
            "1 validation error for list\n__root__\n  Supposed to be an object, but in "
            "reality is a <class 'str'>"
        ),
    ):
        adapter.validate_simdjson(data)


def test_not_an_array():
    adapter = TypeAdapter(list)
    data = dumps("abc")
    with pytest.raises(
        ValueError,
        match=re.escape(
            "1 validation error for list\n__root__\n  Supposed to be an array, but in "
            "reality is a <class 'str'>"
        ),
    ):
        adapter.validate_simdjson(data)


def test_nested_not_an_array():
    adapter = TypeAdapter(List[list])
    data = dumps(["abc"])
    with pytest.raises(
        ValueError,
        match=re.escape(
            "1 validation error for list\n__root__\n  Supposed to be an array, but in "
            "reality is a <class 'str'>"
        ),
    ):
        adapter.validate_simdjson(data)


def test_ok():
    data = [
        {
            "l1_list": [
                {"l2": {"s": "0", "i": 0, "f": 0.0, "other": "value"}},
                {"l2": {"s": "1", "i": 1, "f": 1.0, "another": "value"}},
            ],
        }
    ]
    expected = [
        {
            "l1_list": [
                {"l2": {"s": "0", "i": 0, "f": 0.0}},
                {"l2": {"s": "1", "i": 1, "f": 1.0}},
            ],
            "l1_dict": None,
        }
    ]
    adapter = TypeAdapter(List[ModelNested])
    (parsed,) = adapter.validate_simdjson(dumps(data))
    assert [parsed.model_dump()] == expected


def test_raw_missing_required():
    data = {
        "l1_list": [
            {"l2": {"s": "0", "i": 0}},
        ],
    }
    with pytest.raises(
        ValidationError,
        match=re.escape(
            "1 validation error for ModelNested\nl1_list.0.l2.f\n  Field required "
            "[type=missing, input_value={'s': '0', 'i': 0}, input_type=dict]"
        ),
    ):
        adapter = TypeAdapter(ModelNested)
        adapter.validate_simdjson(dumps(data))
