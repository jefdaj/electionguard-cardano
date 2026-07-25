import pytest
# from tests.env3_generated_networks.lib import *
from ..lib import get_random_seed

@pytest.fixture(scope='session')
def random_seed():
    return get_random_seed()
