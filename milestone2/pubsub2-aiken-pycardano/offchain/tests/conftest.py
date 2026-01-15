import pytest

from pathlib import Path
from pycardano import OgmiosV6ChainContext, SigningKey
from os.path import realpath

from pubsub import load_test_wallet_signing_key, Publisher, CIDv1, OGMIOS_CTX

# TODO is it better to put all fixtures here, or spread them over the relevant test files?

@pytest.fixture
def data_dir() -> Path:
    return Path(__file__).parent / "data"

def election_public_records_flat(data_path: Path) -> [Path]:
    pubdir = data_path / "election-public-records-flat"
    return 

@pytest.fixture(scope="session")
def ogmios() -> OgmiosV6ChainContext:
    """Shared Ogmios connection for all testnet tests."""
    ogmios = OGMIOS_CTX
    try:
        # TODO just query tip and assert that it's a good response
        assert ogmios.last_block_slot > 101181854
        return ogmios
    except:
        raise Exception('Ogmios not up?')

# TODO rename -> wallet and also include addr here?
@pytest.fixture(scope="session")
def sk():
    """Load test publisher signing key."""
    return load_test_wallet_signing_key()

# TODO separate fixture for the test wallet addr?


# TODO example files fixture

# TODO make this depend on the example files and calculate CIDs from them
# TODO then make the subscriber test(s) depend on both the files + cids? or make this a map of cid -> path (or vice versa)
# TODO ah, by combining that with a dependency on test_publish_cids, it should work!
@pytest.fixture(scope="function")
def cids():
    """A few example CIDs"""
    return [
      CIDv1.from_string(s)
      for s in [
        'bafkreib37tosipox6e34euegwwvfdggokcsjklzhpkhx5sbmbbdyece6qy',
        'bafkreieykytgkz3wk5pwe7xlh7rg3zpifje5aopy535r2ptu5p25sr43fm',
        'bafkreihsol6yrmc7lyydvv6ctmvgz54yznsoo5qxybab5p4nzrtyahtsi4'
      ]
    ]
