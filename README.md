# pysimdjson-schemaful

Schema-aware [pysimdjson](https://github.com/TkTech/pysimdjson) loader for
efficient parsing of large excessive JSON inputs.

When working with external APIs you have zero influence on, you may face the
following unfortunate edge-case (as we did):

* Particular endpoint responds with a relatively massive JSON-body, say, ≥ 1 MB.
* The amount of data you really need is several magnitudes smaller, e.g., 1 KB.
* There is no server-side filtering available.

In such a case it may be very excessive in terms of memory, cpu time and delay to
deserialize and, subsequently, validate the whole response, even when using
fast JSON-deseralization libraries, such as
[orjson](https://github.com/ijl/orjson>).

In our particular case we needed less than 0.1% of ~5 MB responses, which we
validated with [pydantic](https://github.com/pydantic/pydantic>).
First, we compared several combinations of deserializers and validators:

* `json` + `pydantic v1` (`Model.parse_raw(json.loads(data))`)
* `orjson` + `pydantic v1` (`Model.parse_raw(orjson.loads(data))`)
* `pysimdjson` + `pydantic v1` (`Model.parse_raw(simdjson.loads(data))`)
* `pydantic v2` (`Model.model_validate_json(data)`)

To our surprise internal `pydantic v2` parser appeared to be ~2-3 times slower
than `json` + `pydantic v1`. The fastest was `orjson` + `pydantic v1`
(~2-3 times faster than `json` and a bit faster than full `simdjson` parsing).
Such a speed-up, however, still comes with excessive memory spending
(as a complete python dict object is created and populated on deserialization).

Thus, we ended up using `pysimdjson` with its fast lazy parsing and manually
iterated over nested JSON objects/arrays and extracted only required keys. It is
ugly, tedious and hard to maintain of course. However, it showed to be several
times faster than `orjson` and decreased memory consumption.


## Table of Contents

* [The crux](#crux)
* [When to use?](#when_use)
* [Installation](#installation)
* [Usage](#usage)
  * [Basic](#usage_basic)
  * [Reusing parser](#usage_reusing_parser)
  * [Pydantic v1](#usage_pydantic_v1)
  * [Pydantic v2](#usage_pydantic_v2)
* [Benchmarks (TBD)](#benchmarks)

## <a name="crux"/> The crux
This package aims to automate the manual labour of lazy loading with pysimdjson.

Simply feed the JSON-schema in and the input data will be traversed
and loaded with pysimdjson accordingly.

Supports
* `pydantic>=1,<3`
* `python>=3.8,<3.12`
* `simdjson>=2,<6` (with caveats)

Does not support complex schemas (it may be not very reasonable from the
practical standpoint anyway), e.g.,
* `anyOf` (`Union[Model1, Model2]`)
* ...

In such cases it will fully (not lazily) load the underlying objects.

## <a name="when_use"/>  When to use?

* [ ] Input JSON data is large relatively to what is needed in there, i.e.,
selectivity is small.
* [ ] Other deserialization methods appear to be slower and/or more memory
consuming.

If you can check all the boxes, then, this package may prove useful to you.
**Never** use it as a default deserialization method: run some benchmarks for
your particular case first, otherwise, it may and will disappoint you.

## <a name="installation"/> Installation

```bash
pip install pysimdjson-schemaful
```

If you need pydantic support
```bash
pip install "pysimdjson-schemaful[pydantic]"
```

## <a name="Usage"/> Usage

### <a name="usage_basic"/> Basic

<!--  name: test_basic -->
```python
import json
from simdjson_schemaful import loads

schema = {
  "type": "array",
  "items": {
    "$ref": "#/definitions/Model"
  },
  "definitions": {
    "Model": {
      "type": "object",
      "properties": {
        "key": {"type": "integer"},
      }
    }
  }
}

data = json.dumps([
    {"key": 0, "other": 1},
    {"missing": 2},
])

parsed = loads(data, schema=schema)

assert parsed == [
    {"key": 0},
    {},
]
```

Example with `additionalProperties`:

<!--  name: test_basic -->
```python
schema = {
  "type": "object",
  "additionalProperties": {
    "$ref": "#/definitions/Model",
  },
  "definitions": {
    "Model": {
      "type": "object",
      "properties": {
        "key": {"type": "integer"},
      }
    }
  }
}

data = json.dumps({
    "some": {"key": 0, "other": 1},
    "other": {"missing": 2},
})

parsed = loads(data, schema=schema)

assert parsed == {
    "some": {"key": 0},
    "other": {},
}
```

### <a name="usage_reusing_parser"/> Reusing parser

With re-used simdjson parser **(recommended when used in a single thread,
otherwise better consult pysimdjson project on thread-safety)**:

<!--  name: test_basic -->
```python
from simdjson import Parser

parser = Parser()
parsed = loads(data, schema=schema, parser=parser)

assert parsed == {
    "some": {"key": 0},
    "other": {},
}
```

### <a name="usage_pydantic_v1"/> Pydantic v1

With model (call `BaseModel.parse_raw_simdjson`):

<!--  name: test_pydantic_v1_model -->
```python
import json
from simdjson_schemaful.pydantic.v1 import BaseModel

class Model(BaseModel):
  key: int

data = json.dumps({"key": 0, "other": 1})

obj = Model.parse_raw_simdjson(data)
```

With type (call `parse_raw_as_simdjson`):

<!--  name: test_pydantic_v1_type -->
```python
import json
from typing import List
from simdjson_schemaful.pydantic.v1 import BaseModel, parse_raw_simdjson_as

class Model(BaseModel):
  key: int

Type = List[Model]

data = json.dumps([
  {"key": 0, "other": 1},
  {"key": 1, "another": 2},
])

obj1, obj2 = parse_raw_simdjson_as(Type, data)
```

### <a name="usage_pydantic_v2"/> Pydantic v2

With model (call `BaseModel.model_validate_simdjson`):

<!--  name: test_pydantic_v2_model -->
```python
import json
from simdjson_schemaful.pydantic.v2 import BaseModel

class Model(BaseModel):
  key: int

data = json.dumps({"key": 0, "other": 1})

obj = Model.model_validate_simdjson(data)
```

With type adapter (call `TypeAdapter.validate_simdjson`)

<!--  name: test_pydantic_v2_type_adapter -->
```python
import json
from typing import List
from simdjson_schemaful.pydantic.v2 import BaseModel, TypeAdapter

class Model(BaseModel):
  key: int

adapter = TypeAdapter(List[Model])

data = json.dumps([
  {"key": 0, "other": 1},
  {"key": 1, "another": 2},
])

obj1, obj2 = adapter.validate_simdjson(data)
```

## <a name="benchmarks"/> Benchmarks

TBD
