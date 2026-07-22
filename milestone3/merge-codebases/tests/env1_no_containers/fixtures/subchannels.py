import pytest
from pycardano import *
from egc import *
import logging

LOG = logging.getLogger(__name__)


## ------ subchannel wallets -------

@pytest.fixture(scope='module')
def guardian1_wallet(keys_dir: Path) -> Wallet:
    w = Wallet.load_or_create(name='guardian1', keys_dir=keys_dir, verbose=False)
    LOG.debug(f'guardian1_wallet: {w}')
    return w

@pytest.fixture(scope='module')
def guardian2_wallet(keys_dir: Path) -> Wallet:
    w = Wallet.load_or_create(name='guardian2', keys_dir=keys_dir, verbose=False)
    LOG.debug(f'guardian2_wallet: {w}')
    return w

@pytest.fixture(scope='module')
def guardian3_wallet(keys_dir: Path) -> Wallet:
    w = Wallet.load_or_create(name='guardian3', keys_dir=keys_dir, verbose=False)
    LOG.debug(f'guardian3_wallet: {w}')
    return w

@pytest.fixture(scope='module')
def device1_wallet(keys_dir: Path) -> Wallet:
    w = Wallet.load_or_create(name='device1', keys_dir=keys_dir, verbose=False)
    LOG.debug(f'device1_wallet: {w}')
    return w

@pytest.fixture(scope='module')
def verifier1_wallet(keys_dir: Path) -> Wallet:
    w = Wallet.load_or_create(name='verifier1', keys_dir=keys_dir, verbose=False)
    LOG.debug(f'verifier1_wallet: {w}')
    return w
