import pytest
from egc import *
import logging

LOG = logging.getLogger(__name__)

### all tests share one cardano node ###

@pytest.fixture(scope='session')
def ogmios() -> OgmiosV6ChainContext:
    ctx = OGMIOS_CTX
    LOG.debug(f'ogmios: {ctx}')
    return ctx
