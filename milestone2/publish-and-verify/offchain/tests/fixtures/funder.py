import pytest
from pycardano import *
from egc import *
from test_utils import global_fixture, per_election_fixture
import logging

LOG = logging.getLogger(__name__)

@global_fixture
def funder_keys() -> KeyPair:
    kp = KeyPair(name='dev', verbose=False) # leave default, global keys_dir
    LOG.info(f'funder_keys: {kp}')
    return kp

@per_election_fixture
def funder(funder_keys: KeyPair) -> Funder:
    f = Funder(key_pair=funder_keys)
    LOG.info(f'funder: {f}')
    try:
        yield f
    finally:
        if f.subscriber is not None:
            f.subscriber.stop()

@per_election_fixture
def init_txb(
        funder: Funder,
        script: ElectionScript,
        admin_vkh: VerificationKeyHash,
    ) -> TransactionBuilder:
    txb = funder._build_init_tx(
        script=script,
        admin_vkh=admin_vkh,
        admin_ada=100
    )
    LOG.info(f'init_txb: {txb}')
    return txb
