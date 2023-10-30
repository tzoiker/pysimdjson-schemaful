from importlib.util import find_spec

import pytest
from simdjson import Parser

collect_ignore_glob = []
if find_spec("pydantic.v1"):
    collect_ignore_glob.append("pydantic/v1/*")
else:
    collect_ignore_glob.append("pydantic/v2/*")


@pytest.fixture(scope="session")
def parser():
    return Parser()
