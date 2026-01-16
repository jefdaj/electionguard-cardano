import pytest

from pathlib import Path
from time import sleep

from pubsub import Publisher, Subscriber, SubscriberConfig, handle_match
from .test_publish import pub_new, pub_closed, pub_open, pub_pub1, pub_pub2, pub_all

# TODO how to handle channel closing?
# TODO one part is the subscriber should stop when it finds a close msg


### fixtures ###

@pytest.fixture(scope="function")
def sub_closed(pub_closed: Publisher):
    since = pub_closed.tip_before_open
    assert isinstance(since, dict)
    cfg = SubscriberConfig(
        since['slot'],
        since['block_hash'],
        since['slot'] + 600, # ~10min
        pub_closed.pubsub_script.policy_id
    )
    sub = Subscriber(cfg, handle_match)
    sub.start() # TODO should this happen automatically?
    # TODO how to properly run it and await result?
    sleep(120) # 2min
    sub.stop()
    return sub

@pytest.fixture(scope="function")
def sub_pub1(pub_pub1: Publisher):
    since = pub_pub1.tip_before_open
    assert isinstance(since, dict)
    cfg = SubscriberConfig(
        since['slot'],
        since['block_hash'],
        since['slot'] + 60,
        pub_pub1.pubsub_script.policy_id
    )
    sub = Subscriber(cfg, handle_match)
    sub.start() # TODO should this happen automatically?
    # TODO how to properly run it and await result?
    sleep(120)
    sub.stop()
    return sub


# TODO sub_open
# TODO sub_pub1
# TODO sub_pub2
# TODO sub_all

@pytest.fixture
def cfg_all() -> SubscriberConfig:
    "Config for subscribing to a historical channel with 81 published CIDs"
    return SubscriberConfig(
        since_slot=101947668,
        since_block='c6860b74b0602981b3e5790f47d081382cdc49ca34c445b9f0e9723a03251626',
        policy_id='9e31dca6f8b69d15d883d0a6db36f4ecaae2cef5db22ad8ccf0ffb4e',
        until_slot=101947752 + 600
        # TODO until_slot not needed because we know this one was closed?
    )

### tests ###

# TODO separate mark for subscribe vs publish?
@pytest.mark.testnet
@pytest.mark.slow
def test_subscribe_all_hardcoded(
    cfg_all: SubscriberConfig,
    election_records: list[tuple[Path, bytes]]
):
    "Subscribe to a hardcoded channel with all 81 election record CIDs"
    sub = Subscriber(cfg_all, handle_match)
    sub.start()
    # TODO come up with a better wait mechanism
    # while not sub._watcher_stop.is_set():
    sleep(30)
    sub.stop()
    cids = list(v for (k, v) in election_records)
    assert sub.subscribed_cids() == cids, "Subscriber CIDs should match election_records"

# TODO double check pytest isn't creating two different pub_closed instances here
@pytest.mark.slow
@pytest.mark.testnet
def test_subscribe_closed(
    sub_closed: Subscriber,
    pub_closed: Publisher
):
    "Subscribe to a channel that was opened + closed immediately"
    assert pub_closed.published_cids  == []
    assert sub_closed.subscribed_cids() == []

# TODO double check pytest isn't creating two different pub_pub1 instances here
@pytest.mark.slow
@pytest.mark.testnet
def test_subscribe_one(
    sub_pub1: Subscriber,
    pub_pub1: Publisher,
    election_records: list[tuple[Path, bytes]]
):
    "Subscribe to a channel with 1 test TX (3 CIDs)"
    tx = pub_pub1.close_channel()
    pub_pub1.wait_for_confirmation(tx)
    # TODO and wait for subscriber to finish here too?
    cids = list(v for (k, v) in election_records[:3])
    assert pub_pub1.published_cids  == cids, "published CIDs should match" # TODO this works,
    assert sub_pub1.subscribed_cids() == cids, "subscribed CIDs should match" # TODO but not this?

@pytest.mark.slow
@pytest.mark.testnet
def test_subscribe_two(
    pub_pub2: Publisher,
    sub_pub2: Subscriber,
    election_records: list[tuple[Path, bytes]]
):
    "Subscribe to a channel with 2 test TXs (6 CIDs)"
    tx = pub_pub2.close_channel()
    pub_pub2.wait_for_confirmation(tx)
    # TODO and wait for subscriber to finish here too?
    cids = list(v for (k, v) in election_records[:6])
    assert pub_pub1.published_cids  == cids
    assert sub_pub1.subscribed_cids() == cids

@pytest.mark.slow
@pytest.mark.testnet
def test_subscribe_all(
    pub_all: Publisher,
    sub_all: Subscriber,
    election_records: list[tuple[Path, bytes]]
):
    "Subscribe to a channel with all 81 election record CIDs"
    tx = pub_all.close_channel()
    pub_all.wait_for_confirmation(tx)
    # TODO and wait for subscriber to finish here too?
    cids = list(v for (k, v) in election_records)
    assert pub_all.published_cids  == cids
    assert sub_all.subscribed_cids() == cids
