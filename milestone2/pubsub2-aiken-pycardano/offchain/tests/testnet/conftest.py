import pytest

from pathlib import Path
from pycardano import OgmiosV6ChainContext, Network, SigningKey
from os.path import realpath

from pubsub import load_test_wallet_signing_key, PubsubClient

@pytest.fixture(scope="session")
def ctx():
    """Shared Ogmios connection for all testnet tests."""
    ctx = OgmiosV6ChainContext(
        host='localhost',
        port=1337,
        network=Network.TESTNET
    )
    try:
        # TODO is there a cleaner way?
        assert ctx.last_block_slot > 101181854
        return ctx
    except:
        raise Exception('Ogmios not up?')

@pytest.fixture(scope="session")
def sk():
    """Load test publisher signing key."""
    return load_test_wallet_signing_key()

# TODO separate fixture for the test wallet addr?

@pytest.fixture(scope="function")
def ps(ctx: OgmiosV6ChainContext, sk: SigningKey):
    """Load a fresh PubsubClient"""
    path = realpath(Path(__file__).parent / "../../../onchain/plutus.json") # TODO export as a constant, but where?
    return PubsubClient(
        chain_context=ctx,
        raw_plutus_json_path=path,
        publisher_signing_key=sk
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
