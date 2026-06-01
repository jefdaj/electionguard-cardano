import pytest
from egc.ogmios import *
from pycardano import OgmiosV6ChainContext

# TODO disambiguate better from the module
@pytest.fixture(scope='session')
def ogmios() -> OgmiosV6ChainContext:
    '''Shared Ogmios connection for all testnet tests.'''
    log.info('ogmios fixture')
    return OGMIOS_CTX


