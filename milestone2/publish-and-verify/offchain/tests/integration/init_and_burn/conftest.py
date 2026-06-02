import pytest
from egc import *

@pytest.fixture(scope='package')
def admin_keys() -> KeyPair:
    raise NotImplementedError

@pytest.fixture(scope='package')
def funder_init_election():
    raise NotImplementedError
