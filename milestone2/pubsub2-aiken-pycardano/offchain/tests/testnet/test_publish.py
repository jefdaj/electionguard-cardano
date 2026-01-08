import pytest

from pathlib import Path

# from pubsub import IPFSClient
from pubsub import PubsubClient, load_test_wallet_signing_key

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
