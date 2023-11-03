import re
from json import dumps

import pytest

from simdjson_schemaful import loads


def test_any_of_fail():
    schema = {
        "anyOf": [{"type": "string"}, {"$ref": "#/definitions/Model"}],
        "definitions": {
            "Model": {
                "type": "object",
                "properties": {"value": {"type": "integer"}},
                "required": ["value"],
            }
        },
    }
    data = dumps({"some": 0, "value": 1})
    loaded = loads(data, schema=schema)
    assert loaded == {"some": 0, "value": 1}


def test_nested_any_of_fail():
    schema = {
        "type": "array",
        "items": {"anyOf": [{"type": "string"}, {"$ref": "#/definitions/Model"}]},
        "definitions": {
            "Model": {
                "type": "object",
                "properties": {"value": {"type": "integer"}},
                "required": ["value"],
            }
        },
    }
    data = dumps([{"some": 0, "value": 1}])
    loaded = loads(data, schema=schema)
    assert loaded == [{"some": 0, "value": 1}]


def test_dict_value_additional_properties_ok():
    schema = {
        "type": "object",
        "additionalProperties": {"$ref": "#/definitions/Model"},
        "definitions": {
            "Model": {
                "type": "object",
                "properties": {"value": {"type": "integer"}},
                "required": ["value"],
            }
        },
    }
    data = dumps({"key": {"some": 0, "value": 1}})
    loaded = loads(data, schema=schema)
    assert loaded == {"key": {"value": 1}}


def test_nested_dict_value_additional_properties_ok():
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "additionalProperties": {"$ref": "#/definitions/Model"},
        },
        "definitions": {
            "Model": {
                "type": "object",
                "properties": {"value": {"type": "integer"}},
                "required": ["value"],
            }
        },
    }
    data = dumps([{"key": {"some": 0, "value": 1}}])
    loaded = loads(data, schema=schema)
    assert loaded == [{"key": {"value": 1}}]


@pytest.mark.parametrize(
    "keyword",
    ("definitions", "$defs"),
)
def test_definitions(keyword):
    schema = {
        "type": "array",
        "items": {"$ref": f"#/{keyword}/Model"},
        "definitions": {
            "Model": {
                "type": "object",
                "properties": {"value": {"type": "integer"}},
            }
        },
    }
    data = dumps([{"some": 0, "value": 1}])
    loaded = loads(data, schema=schema)
    assert loaded == [{"value": 1}]


def test_not_an_object():
    schema = {"type": "object"}
    data = dumps("abc")
    with pytest.raises(
        ValueError,
        match=re.escape("Supposed to be an object, but in reality is a <class 'str'>"),
    ):
        loads(data, schema=schema)


def test_nested_not_an_object():
    schema = {"type": "array", "items": {"type": "object"}}
    data = dumps(["abc"])
    with pytest.raises(
        ValueError,
        match=re.escape("Supposed to be an object, but in reality is a <class 'str'>"),
    ):
        loads(data, schema=schema)


def test_not_an_array():
    schema = {"type": "array", "items": {}}
    data = dumps("abc")
    with pytest.raises(
        ValueError,
        match=re.escape("Supposed to be an array, but in reality is a <class 'str'>"),
    ):
        loads(data, schema=schema)


def test_nested_not_an_array():
    schema = {"type": "array", "items": {"type": "array", "items": {}}}
    data = dumps(["abc"])
    with pytest.raises(
        ValueError,
        match=re.escape("Supposed to be an array, but in reality is a <class 'str'>"),
    ):
        loads(data, schema=schema)


@pytest.mark.parametrize(
    "data,expected",
    [
        (
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
                "l1_dict": {
                    "l2": {"s": "2", "i": 2, "f": 2.0, "other": "value"},
                    "l1_other_list": [{"some": " val"}],
                    "l1_other_dict": {"some": "val"},
                    "l1_other_val": "val",
                },
                "l1_other_list": [{"some": " val"}],
                "l1_other_dict": {"some": "val"},
                "l1_other_val": "val",
            },
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
                "l1_dict": {
                    "l2": {"s": "2", "i": 2, "f": 2.0},
                },
            },
        ),
        (
            {
                "l1_list": [
                    {"l2": {"s": "0"}},
                    {"l2": {"i": 1}},
                    {"l2": {}},
                    {},
                ],
                "l1_dict": {
                    "l2": {"other": "value"},
                },
            },
            {
                "l1_list": [
                    {"l2": {"s": "0"}},
                    {"l2": {"i": 1}},
                    {"l2": {}},
                    {},
                ],
                "l1_dict": {
                    "l2": {},
                },
            },
        ),
    ],
)
def test_complex(parser, data, expected):
    schema = {
        "$ref": "#/definitions/ModelNested",
        "definitions": {
            "Model2": {
                "type": "object",
                "properties": {
                    "s": {"type": "string"},
                    "i": {"type": "integer"},
                    "f": {"type": "number"},
                },
                "required": ["s", "i", "f"],
            },
            "Model1": {
                "type": "object",
                "properties": {
                    "l2": {"$ref": "#/definitions/Model2"},
                    "l2_model_values": {
                        "type": "object",
                        "additionalProperties": {"$ref": "#/definitions/Model2"},
                    },
                },
                "required": ["l2"],
            },
            "ModelNested": {
                "type": "object",
                "properties": {
                    "l1_list": {
                        "type": "array",
                        "items": {"$ref": "#/definitions/Model1"},
                    },
                    "l1_dict": {"$ref": "#/definitions/Model1"},
                },
                "required": ["l1_list", "l1_dict"],
            },
        },
    }
    data = dumps(data)
    loaded = loads(data, schema=schema, parser=parser)
    assert loaded == expected
