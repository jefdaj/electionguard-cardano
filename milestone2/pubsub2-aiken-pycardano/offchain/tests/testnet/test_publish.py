import pytest
from pubsub.types import ChannelDatum
from pubsub.builders import build_publish_tx

from pathlib import Path
from pycardano import OgmiosChainContext, Network

# from pubsub import IPFSClient
from pubsub import PubsubClient, load_test_wallet_signing_key

# TODO fixtures?
# ctx = OgmiosChainContext(
#     ws_url="ws://localhost:1337", # TODO also http?
#     network=Network.TESTNET
# )
# 
# sk = load_test_wallet_signing_key()
# 
# ps = PubsubClient(
#     chain_context=ctx,
#     plutus_json_path="../onchain/plutus.json",
#     signing_key=sk
# )

# TODO get the entire client from a fixture instead?
@pytest.mark.integration
@pytest.mark.slow
def test_open_and_close_channel(ctx: OgmiosV6ChainContext, sk: SigningKey):

    path = Path(__file__) / "../../../onchain/plutus.json" # TODO export as a constant, but where?
    ps = PubsubClient(chain_context=ctx, plutus_json_path=path, signing_key=sk)

    # open channel
    ps.open_channel()
    ps.wait_for_confirmation()

    # Verify PsOpen is on-chain
    validator_utxos = chain_context.utxos("addr_test...")  # validator address
    found_action = any(
        utxo.output.datum == PsOpen()
        for utxo in validator_utxos
    )
    assert found_action, "Action not found at validator address"

    # close channel
    ps.close_channel()
    ps.wait_for_confirmation()

    # Verify PsClose is on-chain
