import pytest
from pycardano import *
from egc import *
from tests.helpers import per_election_fixture
import logging
import time

LOG = logging.getLogger(__name__)

@per_election_fixture
def admin(admin_wallet: Wallet, election_cfg: ElectionConfig) -> AdminNode:
    node_ = AdminNode(wallet=admin_wallet, election_cfg=election_cfg)
    LOG.debug(f'admin: {node_}')
    node_.await_phase(EgcPhase.CONFIG_ANNOUNCE)
    try:
        yield node_
        node_.return_collateral()
    finally:
        node_.stop()
