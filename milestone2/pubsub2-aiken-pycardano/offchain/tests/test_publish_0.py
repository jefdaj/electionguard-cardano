import pytest
from pubsub import *

@pytest.fixture(scope='module')
def pub0_closed(pub0_open: Publisher):
    "Returns a publisher with an already-closed channel"
    pub = pub0_open
    close_tx = pub.close_channel()
    pub.wait_for_confirmation(close_tx)
    return pub

@pytest.mark.testnet
def test_close_nopub(pub0_closed: Publisher):
    assert pub0_closed.channel_state == 'closed', "channel should be closed"
    assert pub0_closed.published_cids == [], "no CIDs should be published"
