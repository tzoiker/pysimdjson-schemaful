import re
from json import dumps

import pytest
from pydantic import ValidationError

from tests.pydantic.v1.conftest import ModelNested


def test_not_an_object():
    data = dumps("abc")
    with pytest.raises(
        ValidationError,
        match=re.escape(
            "Supposed to be an object, but in reality is a <class 'str'>",
        ),
    ):
        ModelNested.parse_raw_simdjson(data)


def test_nested_not_an_object():
    data = dumps({"l1_list": [], "l1_dict": "abc"})
    with pytest.raises(
        ValidationError,
        match=re.escape(
            "Supposed to be an object, but in reality is a <class 'str'",
        ),
    ):
        ModelNested.parse_raw_simdjson(data)


def test_nested_not_an_array():
    data = dumps({"l1_list": "abc"})
    with pytest.raises(
        ValueError,
        match=re.escape("Supposed to be an array, but in reality is a <class 'str'>"),
    ):
        ModelNested.parse_raw_simdjson(data)


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
    parsed = ModelNested.parse_raw_simdjson(dumps(data))
    assert parsed.dict() == expected


def test_missing_required():
    data = {
        "l1_list": [
            {"l2": {"s": "0", "i": 0}},
        ],
    }
    with pytest.raises(
        ValidationError,
        match=re.escape(
            "1 validation error for ModelNested\nl1_list -> 0 -> l2 -> f\n  "
            "field required (type=value_error.missing)"
        ),
    ):
        ModelNested.parse_raw_simdjson(dumps(data))
