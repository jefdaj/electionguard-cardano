import pytest
from pycardano import *
from egc import *
import logging

LOG = logging.getLogger(__name__)

@pytest.fixture(scope='session')
def funder_keys() -> KeyPair:
    kp = KeyPair(name='dev', verbose=False) # leave default, global keys_dir
    return kp

@pytest.fixture(scope='package')
def funder(funder_keys: KeyPair) -> Funder:
    return Funder(key_pair=funder_keys)

@pytest.fixture(scope='package')
def init_tx(
        funder: Funder,
        script: ElectionScript,
        admin_vkh: VerificationKeyHash,
    ) -> TransactionBuilder:
    return funder.build_init_tx(
        script=script,
        admin_vkh=admin_vkh,
        admin_ada=100
    )

# TODO try deploying manually before making a fixture
# TODO should the fixture only be one thing? maybe wait for confirmation and then throw out the tx obj
# @pytest.fixture(scope='package')
# def deploy
