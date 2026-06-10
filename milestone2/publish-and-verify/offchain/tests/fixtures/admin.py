import pytest
from pycardano import *
from egc import *
from test_utils import per_election_fixture
import logging
import time

LOG = logging.getLogger(__name__)

@per_election_fixture
def admin_wallet(keys_dir: Path) -> Wallet:
    w = Wallet.load_or_create(keys_dir=keys_dir, name='admin', verbose=False)
    return w

@per_election_fixture
def admin_vkh(admin_wallet: Wallet) -> VerificationKeyHash:
    return admin_wallet.vkh

@per_election_fixture
def admin_addr(admin_wallet: Wallet) -> Address:
    return admin_wallet.addr

@per_election_fixture
def admin(election: ElectionContext, admin_wallet: Wallet) -> AdminNode:
    node = AdminNode(election=election, wallet=admin_wallet)
    LOG.debug(f'admin: {node}')
    try:
        yield node
    finally:
        node.stop()
