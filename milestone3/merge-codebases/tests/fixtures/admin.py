import pytest
from pycardano import *
from egc import *
from helpers import per_election_fixture
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
def admin(admin_wallet: Wallet, config: ElectionConfig) -> AdminNode:
    # TODO all other nodes should start from config now, not election context!
    # TODO but maybe call it "election" later?
    node_ = AdminNode(wallet=admin_wallet, config=ElectionConfig)
    LOG.debug(f'admin: {node_}')
    try:
        yield node_
        node_.return_collateral()
    finally:
        node_.stop()
