import pytest
from tests.env_3_generated_networks.helpers import *

@pytest.fixture(scope='session')
def random_seed():
    return get_random_seed()
