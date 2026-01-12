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

# @pytest.mark.testnet
# def test_subscribe_hardcoded(ps: PubsubClient):
# 
#     # These are from a previous run of test_publish_cids
#     # TODO provide as a KupoConfig fixture
#     start_slot = 101536192
#     block_hash = 'd08aaae4c359dcf3597c63eff73f7fcc5e92ed053a620c47cce06096f05e29e7'
#     policy_id = '37128f51881775354e479aa2a5daf6876a96b2995597baf4d0b69486'
# 
#     # TODO also provide test files in a dir as a fixture??
# 
#     # only scan 10min of history to speed up the test
#     # TODO subscriber should auto stop when channel is closed too
#     stop_slot = start_slot + 600
# 
#     # TODO write code for this
#     ps.subscribe(start_slot, block_hash, policy_id, stop_slot=stop_slot)
# 
#     # TODO test that the correct files are created
#     # TODO ... which will require adjusting that prev test to upload valid cids and save the files?
#     #          consider whether it would be easier to skip the hardcoding and just test the full cycle directly
