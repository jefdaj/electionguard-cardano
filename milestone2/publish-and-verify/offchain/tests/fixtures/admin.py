import pytest
from pycardano import *
from egc import *
import logging

LOG = logging.getLogger(__name__)

@pytest.fixture(scope='package')
def admin_keys(keys_dir: Path) -> KeyPair:
    kp = KeyPair(keys_dir=keys_dir, name='admin', verbose=False)
    return kp

@pytest.fixture(scope='package')
def admin_vkh(admin_keys: KeyPair) -> VerificationKeyHash:
    return admin_keys.vkh

# TODO rename admin_node?
@pytest.fixture(scope='package')
def admin(election: ElectionContext, admin_keys: KeyPair) -> Admin:
    a = Admin(election=election, key_pair=admin_keys)
    LOG.debug(f'admin: {a}')
    return a
