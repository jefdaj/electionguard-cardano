import pytest
from pycardano import OgmiosChainContext, Network
from pubsub.utils.keys import load_signing_key

@pytest.fixture(scope="session")
def chain_context():
	"""Shared Ogmios connection for all testnet tests."""
	return OgmiosChainContext(
		ws_url="ws://localhost:1337",
		network=Network.TESTNET
	)

@pytest.fixture(scope="session")
def publisher_key():
	"""Load test publisher signing key."""
	return load_signing_key("keys/publisher.skey")

@pytest.fixture
def funded_address(chain_context, publisher_key):
	"""Ensure test address has funds before each test."""
	address = publisher_key.to_verification_key().hash().to_address()
	utxos = chain_context.utxos(address)
	if not utxos:
    	pytest.skip("Test address needs funding on Preview testnet")
	return address
