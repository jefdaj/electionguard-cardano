import pytest

from pathlib import Path
from pycardano import OgmiosV6ChainContext, Network, SigningKey

from pubsub.utils.keys import load_test_wallet_signing_key, PubsubClient

@pytest.fixture(scope="session")
def ctx():
    """Shared Ogmios connection for all testnet tests."""
    return OgmiosChainContext(
        ws_url="ws://localhost:1337", # TODO http too, or instead?
        network=Network.TESTNET
    )

@pytest.fixture(scope="session")
def sk():
    """Load test publisher signing key."""
    return load_test_wallet_signing_key()

# TODO separate fixture for the test wallet addr?

@pytest.fixture(scope="test")
def ps(ctx: OgmiosV6ChainContext, sk: SigningKey):
    """Load a fresh PubsubClient"""
    path = Path(__file__) / "../../../onchain/plutus.json" # TODO export as a constant, but where?
    return PubsubClient(
        chain_context=ctx,
        plutus_json_path=path,
        signing_key=sk
        # ipfs_client=IPFSClient()
    )

# @pytest.fixture
# def funded_address(chain_context, publisher_key):
#     """Ensure test address has funds before each test."""
#     address = publisher_key.to_verification_key().hash().to_address()
#     utxos = chain_context.utxos(address)
#     if not utxos:
#         pytest.skip("Test address needs funding on Preview testnet")
#     return address
