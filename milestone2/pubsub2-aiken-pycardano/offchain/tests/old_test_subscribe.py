import pytest

from pathlib import Path
from time import sleep

from pubsub import Publisher, Subscriber, SubscriberConfig, handle_match
from .test_publish import pub_new, pub_closed, pub_open, pub_pub1, pub_pub2, pub_all

# TODO how to handle channel closing?
# TODO one part is the subscriber should stop when it finds a close msg


### tests ###

# TODO separate mark for subscribe vs publish?
@pytest.mark.testnet
def test_subscribe_all_hardcoded(
    sub_all: Subscriber,
    election_records: list[tuple[Path, bytes]]
):
    "Subscribe to a hardcoded channel with all 81 election record CIDs"
    cids = list(v for (k, v) in election_records)
    assert sub_all.subscribed_cids() == cids, "Subscriber CIDs should match election_records"

# TODO double check pytest isn't creating two different pub_closed instances here
# TODO actually, remove pub_closed entirely?
@pytest.mark.testnet
def test_subscribe_closed(
    sub_closed: Subscriber,
    pub_closed: Publisher
):
    "Subscribe to a channel that was opened + closed immediately"
    assert pub_closed.published_cids  == []
    assert sub_closed.subscribed_cids() == []

# TODO double check pytest isn't creating two different pub_pub1 instances here
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

@pytest.mark.testnet
def test_subscribe_two(
    pub2_live: Publisher,
    sub2_live: Subscriber,
):
    "Subscribe to a channel with 2 test TXs (6 CIDs)"
    # tx = pub_pub2.close_channel()
    # pub_pub2.wait_for_confirmation(tx)
    # TODO and wait for subscriber to finish here too?
    # cids = list(v for (k, v) in election_records[:6])
    assert sub2_live.subscribed_cids() == pub2_live.published_cids

@pytest.mark.testnet
def test_subscribe_all(
    pub_all_live: Publisher,
    sub_all_live: Subscriber,
):
    "Subscribe to a channel with all 81 election record CIDs"
    # tx = pub_all.close_channel()
    # pub_all.wait_for_confirmation(tx)
    # TODO and wait for subscriber to finish here too?
    assert sub_all.subscribed_cids() == pub_all.published_cids
