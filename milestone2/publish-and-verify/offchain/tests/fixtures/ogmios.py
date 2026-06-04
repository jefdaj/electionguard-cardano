import pytest
from egc import *
from test_utils import global_fixture
import logging

LOG = logging.getLogger(__name__)

@global_fixture
def ogmios() -> OgmiosV6ChainContext:
    ctx = OGMIOS_CTX
    LOG.debug(f'ogmios: {ctx}')
    return ctx
