import pytest
# from tests.env3_generated_networks.lib import *
from ..lib import get_random_seed

# TODO get this via hypothesis instead?
@pytest.fixture(scope='session')
def random_seed():
    return get_random_seed()
