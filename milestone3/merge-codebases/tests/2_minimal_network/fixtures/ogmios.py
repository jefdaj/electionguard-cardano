import pytest
from egc import *
# from helpers import global_fixture
# from helpers import per_election_fixture
import logging

LOG = logging.getLogger(__name__)

# @global_fixture
# @pytest.fixture(scope="package")
# @per_election_fixture
@pytest.fixture
def ogmios(arion_network) -> OgmiosV6ChainContext:
    ctx = OGMIOS_CTX
    LOG.debug(f'ogmios: {ctx}')
    return ctx
