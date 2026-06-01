# TODO one session skope funder keypair loaded from disk
# TODO and a package (election) scope Funder object because it'll need a new Subscriber each time

import logging
import pytest

from pycardano import *
from egc.wallet import *

LOG = logging.getLogger(__name__)

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
