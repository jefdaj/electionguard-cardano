import pytest
from time import sleep
from pubsub import *
from .conftest import *


### hardcoded historical channel ###

@pytest.fixture(scope='session')
def cfg_all_hist() -> SubscriberConfig:
    'Config for subscribing to a historical channel with all 81 published CIDs'
    return SubscriberConfig(
        since_slot=101947668,
        since_block='c6860b74b0602981b3e5790f47d081382cdc49ca34c445b9f0e9723a03251626',
        policy_id='9e31dca6f8b69d15d883d0a6db36f4ecaae2cef5db22ad8ccf0ffb4e',
        until_slot=101947752 + 600
        # TODO until_slot not needed because we know this one was closed?
    )

@pytest.fixture(scope='module')
def sub_all_hist(cfg_all_hist: SubscriberConfig) -> Subscriber:
    sub = Subscriber(cfg_all_hist, handle_match, handle_close)
    sub.start()
    # TODO come up with a better wait mechanism
    # while not sub._watcher_stop.is_set():
    sleep(30)
    sub.stop()
    return sub

@pytest.mark.testnet
def test_sub_all_hist(sub_all_hist: Subscriber, cids_all: CIDs):
    assert sub_all_hist.subscribed_cids() == cids_all, 'all CIDs should be fetched'
    assert sub_all_hist.is_done(), 'subscriber should be done'
    # TODO how to test that there's no zombie kupo process?


### live new channel ###

# TODO shorten? currently takes about 7 min
@pytest.fixture(scope='module')
def pub_all_open(pub0_open: Publisher, cids_all: CIDs) -> Publisher:
    'Publisher with all 81 CIDs published in chunks of 10'
    pub = pub0_open
    for cids in chunks(cids_all, 10):
        tx = pub.publish_cids(cids)
        pub.wait_for_confirmation(tx)
    return pub

@pytest.fixture(scope='module')
def pub_all_closed(pub_all_open: Publisher) -> Publisher:
    pub = pub_all_open
    close_tx = pub.close_channel()
    pub.wait_for_confirmation(close_tx)
    return pub

@pytest.mark.testnet
def test_pub_all_open(pub_all_open: Publisher, cids_all: CIDs):
    assert pub_all_open.channel_state == 'published', 'channel should be published'
    assert pub_all_open.published_cids == cids_all, 'all CIDs should be published'

@pytest.mark.testnet
def test_pub_all_closed(pub_all_closed: Publisher, cids_all: CIDs):
    assert pub_all_closed.channel_state == 'closed', 'channel should be closed'
    assert pub_all_closed.published_cids == cids_all, 'all CIDs should be published'

@pytest.fixture(scope='module')
def sub_all_closed(pub_all_closed: Publisher) -> Subscriber:
    since = pub_all_closed.tip_before_open
    assert isinstance(since, dict)
    cfg = SubscriberConfig(
        since['slot'],
        since['block_hash'],
        pub_all_closed.pubsub_script.policy_id,
        since['slot'] + 1200,
    )
    sub = Subscriber(cfg, handle_match, handle_close)
    sub.start()
    sub.join()
    return sub

@pytest.mark.testnet
def test_sub_all_closed(sub_all_closed: Subscriber, cids_all: CIDs):
    assert sub_all_closed.is_done(), 'subscriber should be done'
    assert sub_all_closed.subscribed_cids() == cids_all, 'first two batches of CIDs should be fetched'
