import pytest
from tests.helpers_env3 import get_random_seed

@pytest.fixture(scope='session')
def random_seed():
    return get_random_seed()
