import pytest
from pycardano import *
from egc import *
import logging

LOG = logging.getLogger(__name__)

def test_init_tx(init_tx: Transaction):
    # This verifies that the init_tx fixture burns
    # everything properly after a trivial test.
    LOG.debug(f'init_tx: {init_tx}')
    assert isinstance(init_tx, Transaction)
