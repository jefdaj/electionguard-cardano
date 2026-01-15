import pytest

from pathlib import Path
from typing import List
from pycardano import *

# from pubsub import IPFSClient
from pubsub import Publisher, load_test_wallet_signing_key, CIDv1


### fixtures ###

@pytest.fixture(scope="function")
def pub_new(ogmios: OgmiosV6ChainContext, sk: SigningKey):
    "Load a new Publisher without doing any channel actions"
    return Publisher(
        chain_context=ogmios,
        publisher_signing_key=sk
        # ipfs_client=IPFSClient()
    )

@pytest.fixture(scope="function")
def pub_open(pub_new: Publisher):
    "Yields a publisher with an open channel, then closes it after the test"
    pub = pub_new

    # open channel
    open_tx = pub.open_channel()
    pub.wait_for_confirmation(open_tx)

    # tests using this fixture happen here
    yield pub

    # close channel
    if pub.channel_state != 'closed':
        close_tx = pub.close_channel()
        pub.wait_for_confirmation(close_tx)

@pytest.fixture(scope="function")
def pub_closed(pub_open: Publisher):
    "Returns a publisher with an already-closed channel"
    pub = pub_open
    close_tx = pub.close_channel()
    pub.wait_for_confirmation(close_tx)
    return pub

@pytest.fixture(scope="function")
def pub_pub1(pub_open: Publisher, election_records: list[tuple[Path, bytes]]):
    "Yields a publisher with 1 list of CIDs published, then closes it after the test"
    # TODO is this how the multiple yields should work?
    pub = pub_open

    cids = list(v for (k, v) in election_records[:3])
    # TODO also publish the files via IPFS here
    tx = pub.publish_cids(cids)
    pub.wait_for_confirmation(tx)

    # tests using this fixture happen here
    yield pub

    # close channel
    if pub.channel_state != 'closed':
        close_tx = pub.close_channel()
        pub.wait_for_confirmation(close_tx)

# TODO shorten? currently takes about 7 min
@pytest.fixture(scope="function")
def pub_all(pub_open: Publisher, election_records: list[tuple[Path, bytes]]):

    pub = pub_open
    assert pub.channel_state == 'open'

    for chunk in chunks(election_records, 10):
        cids = list(v for (k, v) in chunk)
        # TODO also publish the files via IPFS here
        tx = pub.publish_cids(cids)
        pub.wait_for_confirmation(tx)
        # assert pub.channel_state == 'published'

    yield pub # TODO will this cause a proper close tx?

@pytest.fixture(scope="function")
def pub_pub2(pub_pub1: Publisher, election_records: list[tuple[Path, bytes]]):
    "Yields (TODO returns?) a publisher with 2 lists of CIDs published, then closes it after the test"
    pub = pub_pub1
    cids = list(v for (k, v) in election_records[3:6]) # TODO off by one?
    tx = pub.publish_cids(cids)
    pub.wait_for_confirmation(tx)
    yield pub
    # TODO will it return to pub_pub1 and close itself here?


### tests ###

@pytest.mark.testnet
@pytest.mark.slow
def test_open(pub_open: Publisher):
    assert pub_open.channel_state == 'open'

@pytest.mark.testnet
@pytest.mark.slow
def test_close_nopub(pub_closed: Publisher):
    pub = pub_closed
    assert pub.channel_state == 'closed'

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

# TODO move to a util module?
def is_suffix(suffix, full):
    if len(suffix) > len(full):
        return False
    return full[-len(suffix):] == suffix

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

# TODO move to a utils module?
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

@pytest.mark.testnet
@pytest.mark.slow
def test_publish_all(pub_all: Publisher, election_records: list[tuple[Path, bytes]]):
    "Publish an entire election worth of CIDs in chunks of 10"
    pub = pub_all
    assert pub.channel_state == 'published'
    actual = pub.published_cids
    expected = [v for (k, v) in election_records]
    assert actual == expected
