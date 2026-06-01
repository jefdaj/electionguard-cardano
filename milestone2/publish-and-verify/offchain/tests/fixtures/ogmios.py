import logging
import pytest

from egc.ogmios import *
from pycardano import OgmiosV6ChainContext

LOG = logging.getLogger(__name__)

# TODO disambiguate better from the module
@pytest.fixture(scope='session')
def ogmios() -> OgmiosV6ChainContext:
    LOG.info('ogmios fixture')
    return OGMIOS_CTX
