import pytest
from pycardano import *
from egc import *
import logging

LOG = logging.getLogger(__name__)

def test_init_and_burn(happy_admin_tx0: Transaction):
    LOG.debug(f'happy_admin_tx0: {happy_admin_tx0}')
    assert isinstance(happy_admin_tx0, Transaction)
