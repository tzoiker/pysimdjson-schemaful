import re
from json import dumps

import pytest
from pydantic import ValidationError

from tests.pydantic.v2.conftest import ModelNested


def test_not_an_object():
    data = dumps("abc")
    with pytest.raises(
        ValidationError,
        match=re.escape(
            "1 validation error for ModelNested\n  Input should be an object "
            "[type=model_type, input_value='abc', input_type=str]",
        ),
    ):
        ModelNested.model_validate_json(data)


def test_nested_not_an_object():
    data = dumps({"l1_list": [], "l1_dict": "abc"})
    with pytest.raises(
        ValidationError,
        match=re.escape(
            "1 validation error for ModelNested\nl1_dict\n  Input should be an "
            "object [type=model_type, input_value='abc', input_type=str]",
        ),
    ):
        ModelNested.model_validate_json(data)


def test_nested_not_an_array():
    data = dumps({"l1_list": "abc"})
    with pytest.raises(
        ValueError,
        match=re.escape(
            "1 validation error for ModelNested\nl1_list\n  Input should be a "
            "valid array [type=list_type, input_value='abc', input_type=str]"
        ),
    ):
        ModelNested.model_validate_json(data)


def test_ok():
    data = {
        "l1_list": [
            {"l2": {"s": "0", "i": 0, "f": 0.0, "other": "value"}},
            {"l2": {"s": "1", "i": 1, "f": 1.0, "another": "value"}},
        ],
        "l1_dict": {
            "l2": {"s": "2", "i": 2, "f": 2.0, "other": "value"},
            "l1_other_list": [{"some": " val"}],
            "l1_other_dict": {"some": "val"},
            "l1_other_val": "val",
        },
        "l1_other_list": [{"some": " val"}],
        "l1_other_dict": {"some": "val"},
        "l1_other_val": "val",
    }
    expected = {
        "l1_list": [
            {"l2": {"s": "0", "i": 0, "f": 0.0}},
            {"l2": {"s": "1", "i": 1, "f": 1.0}},
        ],
        "l1_dict": {
            "l2": {"s": "2", "i": 2, "f": 2.0},
        },
    }
    parsed = ModelNested.model_validate_simdjson(dumps(data))
    assert parsed.model_dump() == expected


def test_missing_required():
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
        ModelNested.model_validate_simdjson(dumps(data))
