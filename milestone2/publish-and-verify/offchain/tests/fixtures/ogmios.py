import pytest
from egc import *

### all tests share one cardano node ###

@pytest.fixture(scope='session')
def ogmios() -> OgmiosV6ChainContext:
    return OGMIOS_CTX
