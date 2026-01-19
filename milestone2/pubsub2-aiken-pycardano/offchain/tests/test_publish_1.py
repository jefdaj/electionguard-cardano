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

@pytest.fixture(scope='module')
def sub1(pub1_closed: Publisher) -> Subscriber:
    since = pub1_closed.tip_before_open
    assert isinstance(since, dict)
    cfg = SubscriberConfig(
        since['slot'],
        since['block_hash'],
        pub1_closed.pubsub_script.policy_id,
        since['slot'] + 300,
    )
    sub = Subscriber(cfg, handle_match, handle_close)
    sub.start()
    sub.join()
    return sub

@pytest.mark.testnet
def test_pub1_open(pub1_open: Publisher, cids1: CIDs):
    assert pub1_open.channel_state == 'published', 'channel should be published'
    assert pub1_open.published_cids == cids1, 'first batch of CIDs should be published'

@pytest.mark.testnet
def test_pub1_closed(pub1_closed: Publisher, cids1: CIDs):
    assert pub1_closed.channel_state == 'closed', 'channel should be closed'
    assert pub1_closed.published_cids == cids1, 'first batch of CIDs should be published'

@pytest.mark.testnet
def test_sub1(sub1: Subscriber, cids1: CIDs):
    assert sub1.is_done(), 'subscriber should be done'
    assert sub1.subscribed_cids() == cids1, 'first batch of CIDs should be fetched'
