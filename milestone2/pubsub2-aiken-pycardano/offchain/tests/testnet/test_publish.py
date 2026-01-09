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

    # TODO Verify PsOpen is on-chain
    # validator_utxos = chain_context.utxos("addr_test...")  # validator address
    # found_action = any(
    #     utxo.output.datum == PsOpen()
    #     for utxo in validator_utxos
    # )
    # assert found_action, "Action not found at validator address"

    # close channel
    close_tx = ps.close_channel()
    ps.wait_for_confirmation(close_tx)

    # TODO Verify PsClose is on-chain

@pytest.mark.testnet
@pytest.mark.slow
def test_publish_cids(ps: PubsubClient, cids: List[CIDv1]):

    # open channel
    open_tx = ps.open_channel()
    ps.wait_for_confirmation(open_tx)
        # TODO Verify PsOpen is on-chain
        # validator_utxos = chain_context.utxos("addr_test...")  # validator address
        # found_action = any(
        #     utxo.output.datum == PsOpen()
        #     for utxo in validator_utxos
        # )
        # assert found_action, "Action not found at validator address"


    # try:
    # pusblish cids

    # TODO huh... it passes when there aren't any CIDs?
    # pub_tx = ps.publish_cids([]) # TODO put them back
    pub_tx = ps.publish_cids(cids)

    ps.wait_for_confirmation(pub_tx)
    # except:
        # raise

    # finally:
    # close channel
    close_tx = ps.close_channel()
    ps.wait_for_confirmation(close_tx)

    # TODO Verify PsClose is on-chain
