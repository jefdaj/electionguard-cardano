import pytest
from pubsub import *
from .conftest import *

@pytest.fixture(scope='module')
def pub1_closed(pub1_open: Publisher):
    "Returns a publisher with an already-closed channel"
    pub = pub1_open
    close_tx = pub.close_channel()
    pub.wait_for_confirmation(close_tx)
    return pub

@pytest.mark.testnet
def test_pub1_open(pub1_open: Publisher, cids1: CIDs):
    assert pub1_closed.channel_state == 'open', 'channel should be open'
    assert pub1_closed.published_cids == cids1, 'first batch of CIDs should be published'

@pytest.mark.testnet
def test_pub1_closed(pub1_closed: Publisher, cids1: CIDs):
    assert pub1_closed.channel_state == 'closed', 'channel should be closed'
    assert pub1_closed.published_cids == cids1, 'first batch of CIDs should be published'
