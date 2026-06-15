import pytest
from egc import *
import logging

LOG = logging.getLogger(__name__)

@pytest.mark.testnet
def test_init_subscriber(election: ElectionContext):
    assert True # TODO write this
