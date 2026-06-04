import pytest
from pycardano import *
from egc import *
import logging

LOG = logging.getLogger(__name__)

@pytest.fixture(scope='session')
def funder_keys() -> KeyPair:
    kp = KeyPair(name='dev', verbose=False) # leave default, global keys_dir
    LOG.info(f'funder_keys: {kp}')
    return kp

@pytest.fixture(scope='package')
def funder(funder_keys: KeyPair) -> Funder:
    f = Funder(key_pair=funder_keys)
    LOG.info(f'funder: {f}')
    return f

@pytest.fixture(scope='package')
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

# TODO try deploying manually before making a fixture
# TODO should the fixture only be one thing? maybe wait for confirmation and then throw out the tx obj
# @pytest.fixture(scope='package')
# def deploy
