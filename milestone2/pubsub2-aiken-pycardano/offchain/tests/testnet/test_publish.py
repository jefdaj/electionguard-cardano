import pytest

from pathlib import Path
from typing import List

# from pubsub import IPFSClient
from pubsub import PubsubClient, load_test_wallet_signing_key, CIDv1

@pytest.mark.testnet
@pytest.mark.slow
def test_open_and_close_channel(ps: PubsubClient):

    # open channel
    open_tx = ps.open_channel()
    ps.wait_for_confirmation(open_tx)

    # close channel
    close_tx = ps.close_channel()
    ps.wait_for_confirmation(close_tx)

@pytest.mark.testnet
@pytest.mark.slow
def test_publish_cids(ps: PubsubClient, cids: List[CIDv1]):

    # open channel
    open_tx = ps.open_channel()
    ps.wait_for_confirmation(open_tx)

    # publish cids
    pub1_tx = ps.publish_cids(cids)
    ps.wait_for_confirmation(pub1_tx)

    # again, to be sure chaining them works
    pub2_tx = ps.publish_cids(cids)
    ps.wait_for_confirmation(pub2_tx)

    # close channel
    close_tx = ps.close_channel()
    ps.wait_for_confirmation(close_tx)
