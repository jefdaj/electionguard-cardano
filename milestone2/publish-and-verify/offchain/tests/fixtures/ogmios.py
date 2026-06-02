from egc import *
import logging
import pytest

LOG = logging.getLogger(__name__)

# TODO disambiguate better from the module
@pytest.fixture(scope='session')
def ogmios() -> OgmiosV6ChainContext:
    LOG.info('ogmios fixture')
    return OGMIOS_CTX
