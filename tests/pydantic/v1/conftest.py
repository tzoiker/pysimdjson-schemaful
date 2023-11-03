from importlib.util import find_spec
from typing import Dict, Optional, Sequence

from pydantic import Extra

# Conftest is imported even when ignored (so have to repeat the check here too)
# https://github.com/pytest-dev/pytest/issues/7452
if not find_spec("pydantic.v1"):
    from simdjson_schemaful.pydantic.v1 import BaseModel

    class Model(BaseModel):
        class Config:
            extra = Extra.forbid

        value: int

    class ModelNested(BaseModel):
        class Model1(BaseModel):
            class Model2(BaseModel):
                s: str
                i: int
                f: float

            l2: Model2
            l2_model_values: Optional[Dict[str, Model2]]

        l1_list: Sequence[Model1]
        l1_dict: Optional[Model1]
