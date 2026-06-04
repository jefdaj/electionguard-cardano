import pytest
from pycardano import *
from egc import *
from test_utils import per_election_fixture
import logging
import time

LOG = logging.getLogger(__name__)

@per_election_fixture
def admin_keys(keys_dir: Path) -> KeyPair:
    kp = KeyPair(keys_dir=keys_dir, name='admin', verbose=False)
    return kp

@per_election_fixture
def admin_vkh(admin_keys: KeyPair) -> VerificationKeyHash:
    return admin_keys.vkh

@per_election_fixture
def admin(election: ElectionContext, admin_keys: KeyPair) -> Admin:
    a = Admin(election=election, key_pair=admin_keys)
    LOG.debug(f'admin: {a}')
    try:
        a.subscriber.start()
        time.sleep(KUPO_DELAY_SEC)
        yield a
    finally:
        a.subscriber.stop()
