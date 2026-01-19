import pytest
from pubsub import *

@pytest.mark.testnet
def test_pub0_open(pub0_open: Publisher):
    assert pub0_open.channel_state == 'open', 'channel should be open'
    assert pub0_open.published_cids == [], 'no CIDs should be published'

@pytest.fixture(scope='module')
def pub0_closed(pub0_open: Publisher) -> Publisher:
    pub = pub0_open
    close_tx = pub.close_channel()
    pub.wait_for_confirmation(close_tx)
    return pub

@pytest.mark.testnet
def test_pub0_closed(pub0_closed: Publisher):
    assert pub0_closed.channel_state == 'closed', 'channel should be closed'
    assert pub0_closed.published_cids == [], 'no CIDs should be published'

@pytest.fixture(scope='module')
def sub0(pub0_closed: Publisher) -> Subscriber:
    since = pub0_closed.tip_before_open
    assert isinstance(since, dict)
    cfg = SubscriberConfig(
        since['slot'],
        since['block_hash'],
        pub0_closed.pubsub_script.policy_id,
        since['slot'] + 300,
    )
    sub = Subscriber(cfg, handle_match, handle_close)
    sub.start() # TODO should this happen automatically?
    sub.join()  # TODO should there also be a timeout in case it fails?
    return sub

@pytest.mark.testnet
def test_sub0(sub0: Subscriber):
    assert sub0.is_done(), 'subscriber should be done'
    assert sub0.subscribed_cids() == [], 'no CIDs should be fetched'
    # TODO how to test that there's no zombie kupo process?
