import pytest
from pycardano import *
from egc import *
import logging

LOG = logging.getLogger(__name__)

@pytest.mark.testnet
def test_burn_admin_stt(init_tx: Transaction):
    # When cleanup succeeds, it verifies that the init_tx fixture burns
    # the admin STT properly after a trivial test.
    LOG.debug(f'init_tx: {init_tx}')
    assert isinstance(init_tx, Transaction)
