import pytest

from pathlib import Path
from typing import List
from pycardano import *

# from pubsub import IPFSClient
from pubsub import Publisher, load_test_wallet_signing_key, CIDv1


### tests ###

@pytest.mark.testnet
@pytest.mark.slow
def test_open(pub_open: Publisher):
    assert pub_open.channel_state == 'open'

@pytest.mark.testnet
@pytest.mark.slow
def test_publish_one(pub_open: Publisher, election_records: list[tuple[Path, bytes]]):
    "Publish the first file to an open channel"
    pub = pub_open
    assert pub.channel_state == 'open'
    cids = list(v for (k, v) in election_records[:3])
    # TODO also publish the files via IPFS here
    tx = pub.publish_cids(cids)
    pub.wait_for_confirmation(tx)
    assert pub.channel_state == 'published'
    assert pub.published_cids == cids

@pytest.mark.testnet
@pytest.mark.slow
def test_close_pub1(pub_pub1: Publisher):
    pub = pub_pub1
    assert pub.channel_state == 'published'
    tx = pub.close_channel()
    pub.wait_for_confirmation(tx)
    assert pub.channel_state == 'closed'

@pytest.mark.testnet
@pytest.mark.slow
def test_publish_two(pub_pub1: Publisher, election_records: list[tuple[Path, bytes]]):
    "Publish a 2nd list of CIDs to a channel that already published one"
    pub = pub_pub1
    assert pub.channel_state == 'published'
    cids = list(v for (k, v) in election_records[3:6]) # TODO off by one?
    # TODO also publish the files via IPFS here
    tx = pub.publish_cids(cids)
    pub.wait_for_confirmation(tx)
    assert pub.channel_state == 'published'
    assert is_suffix(cids, pub.published_cids)

@pytest.mark.testnet
@pytest.mark.slow
def test_publish_all(pub_all: Publisher, election_records: list[tuple[Path, bytes]]):
    "Publish an entire election worth of CIDs in chunks of 10"
    pub = pub_all
    assert pub.channel_state == 'published'
    actual = pub.published_cids
    expected = [v for (k, v) in election_records]
    assert actual == expected
