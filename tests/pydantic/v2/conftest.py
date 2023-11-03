from importlib.util import find_spec
from typing import Optional, Sequence

from pydantic import ConfigDict

# Conftest is imported even when ignored (so have to repeat the check here too)
# https://github.com/pytest-dev/pytest/issues/7452
if find_spec("pydantic.v1"):
    from simdjson_schemaful.pydantic.v2 import BaseModel

    class Model(BaseModel):
        model_config = ConfigDict(extra="forbid")

        value: int

    class ModelNested(BaseModel):
        class Model1(BaseModel):
            class Model2(BaseModel):
                s: str
                i: int
                f: float

            l2: Model2
            l2_model_values: Optional[dict[str, Model2]] = None

        l1_list: Sequence[Model1]
        l1_dict: Optional[Model1] = None
