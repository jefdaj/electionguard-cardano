import json
import pytest

from pathlib import Path
from pycardano import OgmiosV6ChainContext, SigningKey
from os.path import realpath, join

from typing import Dict

from pubsub import load_test_wallet_signing_key, Publisher, CIDv1, OGMIOS_CTX

# TODO is it better to put all fixtures here, or spread them over the relevant test files?

@pytest.fixture
def data_dir() -> Path:
    return Path(__file__).parent / "data"

# TODO remove?
ElectionRecord  = tuple[Path, bytes]
ElectionRecords = list[ElectionRecord]

@pytest.fixture
def election_records(data_dir: Path) -> ElectionRecords:
    records_dir = data_dir / "election_records_flat"
    json_path   = data_dir / "election_records_flat_cids.json"
    with open(json_path, 'r') as f:
        data = json.load(f)
    data = [
        (Path(join(records_dir, k + '.json')), CIDv1.from_string(v))
        for k, v in data.items()
    ]
    return data

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
