import pytest

from pathlib import Path
from pycardano import OgmiosChainContext, Network

# from pubsub import IPFSClient
from pubsub import PubsubClient, load_test_wallet_signing_key

@pytest.mark.integration
@pytest.mark.slow
def test_open_and_close_channel(ps: PubsubClient):

    # open channel
    ps.open_channel()
    ps.wait_for_confirmation()

    # TODO Verify PsOpen is on-chain
    # validator_utxos = chain_context.utxos("addr_test...")  # validator address
    # found_action = any(
    #     utxo.output.datum == PsOpen()
    #     for utxo in validator_utxos
    # )
    # assert found_action, "Action not found at validator address"

    # close channel
    ps.close_channel()
    ps.wait_for_confirmation()

    # TODO Verify PsClose is on-chain
