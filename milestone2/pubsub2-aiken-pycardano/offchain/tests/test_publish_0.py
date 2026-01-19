import pytest
from pubsub import *

@pytest.mark.testnet
def test_pub0_open(pub0_open: Publisher):
    assert pub0_open.channel_state == 'open', 'channel should be open'
    assert pub0_open.published_cids == [], 'no CIDs should be published'

@pytest.fixture(scope='module')
def pub0_closed(pub0_open: Publisher):
    pub = pub0_open
    close_tx = pub.close_channel()
    pub.wait_for_confirmation(close_tx)
    return pub

@pytest.mark.testnet
def test_pub0_closed(pub0_closed: Publisher):
    assert pub0_closed.channel_state == 'closed', 'channel should be closed'
    assert pub0_closed.published_cids == [], 'no CIDs should be published'
