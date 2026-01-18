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
def test_pub1_closed(pub1_closed: Publisher, election_records: ElectionRecords):
    assert pub1_closed.channel_state == 'closed', "channel should be closed"
    assert len(pub1_closed.published_cids) == 3, "3 CIDs should be published"
