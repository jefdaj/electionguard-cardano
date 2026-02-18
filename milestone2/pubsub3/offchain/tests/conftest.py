import json
import pytest

from os.path import realpath, join, exists
from pathlib import Path
from pycardano import OgmiosV6ChainContext, SigningKey
from typing import Dict, List

from pubsub import *


### utilities ###

def is_suffix(suffix, full):
    if len(suffix) > len(full):
        return False
    return full[-len(suffix):] == suffix

def chunks(lst, n):
    '''Yield successive n-sized chunks from lst.'''
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


### misc fixtures ###


@pytest.fixture(scope='session')
def ogmios() -> OgmiosV6ChainContext:
    '''Shared Ogmios connection for all testnet tests.'''
    ogmios = OGMIOS_CTX
    try:
        # TODO just query tip and assert that it's a good response
        assert ogmios.last_block_slot > 101181854
        return ogmios
    except:
        raise Exception('Ogmios not up?')

# TODO rename -> wallet and also include addr here?
@pytest.fixture(scope='session')
def sk():
    '''Load test publisher signing key.'''
    return load_test_wallet_signing_key()


### test data ###

# TODO move these somewhere?
ElectionRecord  = tuple[Path, bytes]
ElectionRecords = list[ElectionRecord]
CID  = bytes
CIDs = list[CID]

@pytest.fixture(scope='session')
def data_dir() -> Path:
    return Path(__file__).parent / 'data'

@pytest.fixture(scope='session')
def election_records(data_dir: Path) -> ElectionRecords:
    records_dir = data_dir / 'election_records_flat'
    json_path   = data_dir / 'election_records_flat_cids.json'
    with open(json_path, 'r') as f:
        data = json.load(f)
    data = [
        (Path(join(records_dir, k + '.json')), CIDv1.from_string(v))
        for k, v in data.items()
    ]
    return data

@pytest.fixture(scope='session')
def cids_all(election_records: ElectionRecords) -> CIDs:
    'All CIDs from the test election records'
    return list(v for (k, v) in election_records)

@pytest.fixture(scope='session')
def cids1(cids_all: CIDs) -> CIDs:
    'First batch of test CIDs to publish'
    return cids_all[:3] # 3 this time

@pytest.fixture(scope='session')
def cids2(cids_all: CIDs) -> CIDs:
    'Second batch of test CIDs to publish'
    return cids_all[3:8] # 5 this time


### publisher fixtures ###

@pytest.fixture(scope='module')
def pub0_new(ogmios: OgmiosV6ChainContext, sk: SigningKey):
    'Load a new Publisher without doing any channel actions'
    return Publisher(
        chain_context=ogmios,
        publisher_signing_key=sk
        # ipfs_client=IPFSClient()
    )

@pytest.fixture(scope='module')
def pub0_open(pub0_new: Publisher):
    '''
    Yields a publisher with an open channel, then closes it after the test.
    This one is special because it burns the channel STT (closes the channel).
    All the other testnet tests should derive from it in order to clean up
    after themselves properly.
    '''
    pub = pub0_new

    # open channel
    open_tx = pub.open_channel()
    pub.wait_for_confirmation(open_tx)

    # tests using this fixture happen here
    # (including dependent fixtures)
    yield pub

    # close channel
    if pub.channel_state != 'closed':
        close_tx = pub.close_channel()
        pub.wait_for_confirmation(close_tx)

@pytest.fixture(scope='module')
def pub1_open(pub0_open: Publisher, cids1: CIDs) -> Publisher:
    'A publisher with 1 list of CIDs published'
    pub = pub0_open
    tx = pub.publish_cids(cids1)
    pub.wait_for_confirmation(tx)
    return pub


### subscriber fixtures ###
