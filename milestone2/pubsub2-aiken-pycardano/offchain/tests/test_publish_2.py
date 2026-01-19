import pytest
from pubsub import *
from .conftest import *

@pytest.fixture(scope='module')
def pub2_closed(pub2_open: Publisher):
    pub = pub2_open
    close_tx = pub.close_channel()
    pub.wait_for_confirmation(close_tx)
    return pub

@pytest.mark.testnet
def test_pub2_open(pub2_open: Publisher, cids1: CIDs, cids2: CIDs):
    cids = cids1 + cids2
    assert pub2_open.channel_state == 'open', 'channel should be open'
    assert pub2_closed.published_cids == cids, 'first 2 batches of CIDs should be published'

@pytest.mark.testnet
def test_pub2_closed(pub2_closed: Publisher, cids1: CIDs, cids2: CIDs):
    cids = cids1 + cids2
    assert pub2_closed.channel_state == 'closed', 'channel should be closed'
    assert pub2_closed.published_cids == cids, 'first 2 batches of CIDs should be published'
