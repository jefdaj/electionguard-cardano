import pytest
from pubsub import *
from .conftest import *

@pytest.fixture(scope='module')
def pub2_open(pub1_open: Publisher, cids2: CIDs) -> Publisher:
    'A publisher with 2 lists of CIDs published'
    pub = pub1_open
    tx = pub.publish_cids(cids2)
    pub.wait_for_confirmation(tx)
    return pub

@pytest.fixture(scope='module')
def pub2_closed(pub2_open: Publisher):
    pub = pub2_open
    close_tx = pub.close_channel()
    pub.wait_for_confirmation(close_tx)
    return pub

@pytest.mark.testnet
def test_pub2_open(pub2_open: Publisher, cids1: CIDs, cids2: CIDs):
    cids = cids1 + cids2
    assert pub2_open.channel_state == 'published', 'channel should be published'
    assert pub2_open.published_cids == cids, 'first 2 batches of CIDs should be published'

@pytest.mark.testnet
def test_pub2_closed(pub2_closed: Publisher, cids1: CIDs, cids2: CIDs):
    cids = cids1 + cids2
    assert pub2_closed.channel_state == 'closed', 'channel should be closed'
    assert pub2_closed.published_cids == cids, 'first 2 batches of CIDs should be published'

@pytest.fixture(scope='module')
def sub2_closed(pub2_closed: Publisher) -> Subscriber:
    since = pub2_closed.tip_before_open
    assert isinstance(since, dict)
    cfg = SubscriberConfig(
        since['slot'],
        since['block_hash'],
        pub2_closed.pubsub_script.policy_id,
        since['slot'] + 600,
    )
    sub = Subscriber(cfg, handle_match, handle_close)
    sub.start()
    sub.join()
    return sub

@pytest.mark.testnet
def test_sub2_closed(sub2_closed: Subscriber, cids1: CIDs, cids2: CIDs):
    cids = cids1 + cids2
    assert sub2_closed.is_done(), 'subscriber should be done'
    assert sub2_closed.subscribed_cids() == cids, 'first two batches of CIDs should be fetched'
