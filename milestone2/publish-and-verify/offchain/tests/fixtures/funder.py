import logging
import pytest

LOG = logging.getLogger(__name__)

from pycardano import *
from egc.wallet import *
from egc.roles.funder import *


### dev keypair with tADA is session scoped ###

@pytest.fixture(scope='session')
def funder_sk() -> SigningKey:
    LOG.debug('funder_sk fixture')
    return load_wallet_signing_key(name='dev')

@pytest.fixture(scope='session')
def funder_addr() -> Address:
    LOG.info('funder_addr fixture')
    return load_wallet_addr(name='dev')

@pytest.fixture(scope='session')
def funder_vkh(funder_sk: SigningKey) -> VerificationKeyHash:
    LOG.info('funder_vkh fixture')
    return vkh_for_signing_key(funder_sk)


### Funder is package scoped because a new Election needs a new Subscriber ###

@pytest.fixture(scope='package')
def funder(
        funder_sk: SigningKey,
        funder_addr: Address,
        funder_vkh: VerificationKeyHash,
    ) -> Funder:
    pass
